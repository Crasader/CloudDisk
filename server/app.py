import hashlib
import os
import shutil
import datetime
import base64

from Crypto.Cipher import AES
from Crypto.Util import Counter
import peewee
from flask import Flask, jsonify, request, send_file
from peewee import *
from itsdangerous import (TimedJSONWebSignatureSerializer as URLSafeSerializer, BadSignature, SignatureExpired)
from functools import wraps
from flask_cors import CORS, cross_origin
from playhouse.shortcuts import model_to_dict, dict_to_model

from DAO import *

app = Flask(__name__)
app.config.from_object('config')
# 允许跨域
CORS(app)


def verify_auth_token(token):
    s = URLSafeSerializer(app.config['SECRET_KEY'])
    try:
        data = s.loads(token)
    except SignatureExpired:
        return None
    except BadSignature:
        return None
    return 'key' in data and data['key'] == app.config['SECRET_KEY']


def test_authorization():
    cookies = request.cookies
    headers = request.headers
    args = request.args
    token = None
    if 'token' in cookies:
        token = cookies['token']
    elif 'Authorization' in headers:
        token = headers['Authorization']
    elif 'token' in args:
        token = args['token']
    else:
        return False
    return verify_auth_token(token)


def authorization_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not test_authorization():
            return jsonify(message='unauthorized'), 401
        return f(*args, **kwargs)

    return wrapper


def generate_path(fid, pfolder, pchild):
    actual_path = pchild
    if fid != 0:
        actual_path = pfolder + '/' + pchild
    return actual_path


def AES_Encrypt(data):
    vi = '0918273645abcdef'
    pad = lambda s: s + (16 - len(s) % 16) * chr(16 - len(s) % 16)
    data = pad(data)
    cipher = AES.new(app.config['DES_KEY'].encode('utf8'), AES.MODE_CBC, vi.encode('utf8'))
    encryptedbytes = cipher.encrypt(data.encode('utf8'))
    encodestrs = base64.b64encode(encryptedbytes)
    enctext = encodestrs.decode('utf8')
    return enctext


def AES_Decrypt(data):
    vi = '0918273645abcdef'
    data = data.encode('utf8')
    encodebytes = base64.decodebytes(data)
    cipher = AES.new(app.config['DES_KEY'].encode('utf8'), AES.MODE_CBC, vi.encode('utf8'))
    text_decrypted = cipher.decrypt(encodebytes)
    unpad = lambda s: s[0:-s[-1]]
    text_decrypted = unpad(text_decrypted)
    text_decrypted = text_decrypted.decode('utf8')
    return text_decrypted


def get_encrypt_url(obj):
    data = ''
    if isinstance(obj, File):
        data = 'fi '
    elif isinstance(obj, Folder):
        data = 'fo '
    else:
        return None
    data += str(obj.id).zfill(64)
    url = AES_Encrypt(data)
    print(url)
    return url


def get_decrypt_url(url):
    data = AES_Decrypt(url)
    print(data)
    srcdata = data.split(' ')
    if len(srcdata) != 2:
        return None
    print(srcdata)
    return srcdata


def get_file_download_path(file):
    folderpath = Folder.select(Folder.path).where(Folder.id == file.folderid)
    actual_path = generate_path(file.folderid, folderpath.path, file.name)
    target_file = os.path.join(os.path.expanduser(app.config['UPLOAD_FOLDER']), actual_path)
    if os.path.exists(actual_path):
        rv = send_file(target_file, as_attachment=True, attachment_filename=file.name)
        return rv
    return None


@app.route('/login', methods=['POST'])
def login():
    req = request.get_json()
    # 验证用户名密码
    if req['email'] == app.config['EMAIL'] and req['password'] == app.config['PASSWORD']:
        # 生成 Token，有效期为一周
        s = URLSafeSerializer(app.config['SECRET_KEY'], expires_in=7 * 24 * 3600)

        return jsonify(message='OK',
                       token=s.dumps({'key': app.config['SECRET_KEY']}).decode('utf-8'))
    else:
        return jsonify(message='unauthorized'), 401


@app.route('/auth', methods=['GET'])
@authorization_required
def auth():
    return jsonify(message='OK')


@app.route('/folders', methods=['GET', 'POST'])
# TODO: @authorization_required
def folders():
    if request.method == 'POST':
        req = request.get_json()
        foldername = req['name']
        parentid = req['parentid']
        folder = Folder.get_by_id(parentid)
        # folderpath = foldername
        # if parentid != 0:
        #     folderpath = folder.path + '/' + foldername

        folderpath = generate_path(parentid, folder.path, foldername)
        target_folder = os.path.join(os.path.expanduser(app.config['UPLOAD_FOLDER']), folderpath)
        if os.path.exists(target_folder):
            return jsonify(message='error'), 409
        try:
            os.mkdir(target_folder)
            f = Folder.create(name=foldername, path=folderpath, parentid=parentid, isShared=False,
                              isShareEncryped=False, sharePassword="", shareUrl="", sharePeriod=datetime.datetime.now())
            f.save()
            return jsonify(message='OK'), 201
        except peewee.IntegrityError as e:
            return jsonify(message="error"), 409
        except Exception as e:
            app.logger.exception(e)
            return jsonify(message="error"), 409
    if request.method == 'GET':
        query = Folder.select()
        if query.exists():
            return jsonify(message='ok', data=[model_to_dict(folder) for folder in query])
        else:
            return jsonify(message='ok', data=[])


@app.route('/folders/<folder_id>', methods=['GET', 'POST', 'DELETE', 'PATCH'])
# TODO: @authorization_required
def folder(folder_id):
    try:
        folder = Folder.get_by_id(folder_id)
    except peewee.DoesNotExist:
        return jsonify(message='error'), 404
    if request.method == 'GET':
        subfolders = Folder.select().where(Folder.parentid == folder.id)
        files = File.select().where(File.folderid == folder_id)
        subfolderList = []
        for subfolder in subfolders:
            if subfolder.id != 0:
                subfolderList.append(model_to_dict(subfolder))
        return jsonify(message='OK', data=model_to_dict(folder, backrefs=True),
                       subfolders=subfolderList,
                       files=[model_to_dict(file) for file in files])
    elif request.method == 'DELETE':
        folderpath = folder.path
        target_file = os.path.join(os.path.expanduser(app.config['UPLOAD_FOLDER']), folderpath)
        try:
            # 递归删除数据库函数
            def recuesiondel(folder_id):
                files = File.select().where(File.folderid == folder_id)
                for file in files:
                    file.delete_instance()
                subfolders = Folder.select().where(Folder.parentid == folder_id)
                for subfolder in subfolders:
                    recuesiondel(subfolder.id)
                    subfolder.delete_instance()

            # 递归删除数据库
            recuesiondel(folder_id)
            # 删除文件夹
            shutil.rmtree(target_file)
            # 数据库删除自身
            folder.delete_instance()

        except peewee.IntegrityError:
            return jsonify(message='error'), 409
        except Exception as e:
            app.logger.exception(e)
            return jsonify(message='error'), 409
    elif request.method == 'POST':
        file = request.files['file']
        if file:
            # filepath = file.filename
            # if folder_id != '0':
            #     filepath = folder.path + '/' + file.filename
            filepath = generate_path(folder_id, folder.path, file.filename)
            target_file = os.path.join(os.path.expanduser(app.config['UPLOAD_FOLDER']), filepath)
            print(folder_id)
            print(filepath)
            print(target_file)
            if os.path.exists(target_file):
                return jsonify(message='error'), 409
            try:
                file.save(target_file)
                f = File.create(folder=folder, name=file.filename, folderid=folder_id,
                                isShareEncryped=False, sharePassword="", shareUrl="",
                                sharePeriod=datetime.datetime.now())
                f.save()
            except Exception as e:
                app.logger.exception(e)
                return jsonify(message='error'), 500
    elif request.method == 'PATCH':
        req = request.get_json()
        folder.isShared = req['isShare']
        if folder.isShared:
            folder.isShareEncryped = req['isShareEncryped']
            folder.shareUrl = get_encrypt_url(folder)
            folder.sharePeriod = datetime.datetime.now() + datetime.timedelta(req['sharePeriod']);
            if folder.isShareEncryped:
                folder.sharePassword = req['sharePassword']
        folder.save()
    return jsonify(message='OK')


@app.route('/files/<file_id>', methods=['GET', 'DELETE', 'PATCH'])
# TODO: @authorization_required
def files(file_id):
    # actual_filename = generate_filename(folder_id, filename)

    try:
        file = File.get_by_id(file_id)
    except peewee.DoesNotExist:
        return jsonify(message='error'), 404
    # actual_path = file.name
    # if file.folderid != 0:
    #     folderpath = Folder.select(Folder.path).where(Folder.id == file.folderid)
    #     actual_path = folderpath + '/' + file.name
    folderpath = Folder.get(Folder.id == file.folderid)
    actual_path = generate_path(file.folderid, folderpath.path, file.name)
    target_file = os.path.join(os.path.expanduser(app.config['UPLOAD_FOLDER']), actual_path)
    if request.method == 'GET':
        args = request.args
        if 'query' in args and args['query'] == 'info':
            return jsonify(message='OK', data=model_to_dict(file), actual_path=actual_path)
        if os.path.exists(target_file):
            return send_file(target_file)
        else:
            return jsonify(message='error'), 404
    elif request.method == 'DELETE':
        if os.path.exists(target_file):
            try:
                file.delete_instance()
                os.remove(target_file)
                return jsonify(message='OK')
            except Exception as e:
                app.logger.exception(e)
                return jsonify(message='error'), 500
        else:
            return jsonify(message='error'), 404
    elif request.method == 'PATCH':
        req = request.get_json()
        file.isShared = req['isShare']
        if file.isShared:
            file.isShareEncryped = req['isShareEncryped']
            file.shareUrl = get_encrypt_url(file)
            file.sharePeriod = datetime.datetime.now() + datetime.timedelta(req['sharePeriod']);
            if file.isShareEncryped:
                file.sharePassword = req['sharePassword']
        file.save()
    return jsonify(message='OK')


@app.route('/share/<path>', methods=['GET'])
def share(path):
    res = get_decrypt_url(path)
    args = request.args
    if res:
        if res[0] == 'fi':
            print(int(res[1]))
            try:
                file = File.get_by_id(int(res[1]))
            except peewee.DoesNotExist:
                return jsonify(message='error'), 404
            if file.isShared:
                if file.isShareEncryped:
                    if 'download' in args and args['download'] == 'true' and \
                            'password' in args and args['password'] == file.sharePassword:
                        rv = get_file_download_path(file)
                        if rv:
                            return rv
                        else:
                            return jsonify(message='error'), 404
                    else:
                        return jsonify(message='error'), 409
                else:
                    if 'download' in args and args['download'] == 'true':
                        rv = get_file_download_path(file)
                        if rv:
                            return rv
                        else:
                            return jsonify(message='error'), 404
                    else:
                        return jsonify(message='ok', type="file", filename=file.name)
            else:
                return jsonify(message='error'), 409
        elif res[0] == 'fo':
            print(int(res[1]))
        else:
            return jsonify(message='error'), 409
    else:
        return jsonify(message='error'), 409
    return jsonify(message='OK')


if __name__ == '__main__':
    app.run(debug=True)

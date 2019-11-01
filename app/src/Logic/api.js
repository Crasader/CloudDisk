const Api = {
    SERVER_API: 'http://localhost:5000',

    login(email, password) {
        return fetch(this.SERVER_API + "/login", {
            method: 'POST',
            body: JSON.stringify({email: email, password: password}),
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
        });
    },

    // 由于跨域的问题，我们暂时不能使用 Cookie 来认证，这里改用 Header 进行认证
    auth(token) {
        return fetch(this.SERVER_API + "/auth", {
            method: 'GET',
            headers: {
                'Authorization': token,
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
        });
    },

    getFolders() {
        return fetch(this.SERVER_API + "/folders", {
            method: 'GET',
            headers: {
                'Accept': 'application/json'
            }
        });
    },
    getFolder(id) {
        return fetch(this.SERVER_API + '/folders/' + id, {
            method: 'GET',
            headers: {
                'Accept': 'application/json'
            }
        });
    },
    addFolder(name, id) {
        return fetch(this.SERVER_API + "/folders", {
            method: 'POST',
            body: JSON.stringify({name: name, parentid: id}),
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        });
    },
    deleteFolder(id) {
        return fetch(this.SERVER_API + '/folders/' + id, {
            method: 'DELETE',
            headers: {
                'Accept': 'application/json'
            }
        });
    },
    uploadFile(folderid, file) {
        let data = new FormData();
        data.append('file', file);
        return fetch(this.SERVER_API + '/folders/' + folderid, {
            method: 'POST',
            body: data,
            headers: {
                'Accept': 'application/json'
            }
        });
    },
    deleteFile(fileid) {
        return fetch(this.SERVER_API + '/files/' + fileid, {
            method: 'DELETE',
            headers: {
                'Accept': 'application/json',
            }
        });
    },
    downloadFile(fileid) {
        return this.SERVER_API + '/files/' + fileid;
    }

};

export default Api;
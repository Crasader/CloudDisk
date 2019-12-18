#ifndef SERVERCONNECT_H
#define SERVERCONNECT_H

#include <QMap>
#include <QObject>
#include <QNetworkRequest>
#include <QNetworkReply>
#include <QNetworkAccessManager>
#include <QJsonObject>
#include <QJsonDocument>

#include <QAbstractNetworkCache>
#include <QJsonDocument>

#include "class_global/setting.h"

class ServerConnect : QObject
{
    Q_OBJECT
public:

private:
    static ServerConnect* serverConnect;
    static QNetworkAccessManager* accessManager;


public:
    ServerConnect();
    ~ServerConnect();

    static ServerConnect& getInstance();
    QNetworkAccessManager* getNetworkAccessManager();

    QNetworkReply* http_get(QString url, QMap<QString, QString> param = QMap<QString, QString>());
    QNetworkReply* http_post(QString url, QJsonDocument jsonData = QJsonDocument());
    QNetworkReply* http_post(QString url,  QHttpMultiPart* multiPart);

    QNetworkReply* http_delete(QString url);
    QNetworkReply* http_patch(QString url, QJsonDocument jsonData);

    QNetworkReply* http_get_download(QString url, bool isBreakpointResumeModel, qint64 breakpoint);

private:
    void CreateConnect();

public slots:
    void requestCallback(QNetworkReply* reply);

};

#endif // SERVERCONNECT_H

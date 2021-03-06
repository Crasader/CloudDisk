#ifndef LOGIN_H
#define LOGIN_H

#include <QDialog>
#include <QNetworkRequest>
#include <QNetworkReply>
#include <QNetworkAccessManager>
#include <QJsonObject>
#include <QJsonDocument>

#include "serverconnect.h"

namespace Ui
{
    class LogIn;
}

class LogIn : public QDialog
{
    Q_OBJECT

public:
    explicit LogIn(QWidget* parent = nullptr);
    ~LogIn();

private:
    Ui::LogIn* ui;

    enum class requestType {LOGIN, AUTH};
    QMap<QNetworkReply*, requestType> replyMap;

private slots:
    void login();
    void response(QNetworkReply* reply);

};

#endif // LOGIN_H

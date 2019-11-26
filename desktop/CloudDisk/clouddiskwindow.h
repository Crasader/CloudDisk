#ifndef CLOUDDISKWINDOW_H
#define CLOUDDISKWINDOW_H

#include <QMainWindow>
#include "login.h"

namespace Ui
{
    class CloudDiskWindow;
}

class CloudDiskWindow : public QMainWindow
{
    Q_OBJECT

public:
    explicit CloudDiskWindow(QWidget* parent = nullptr);
    ~CloudDiskWindow();

private:
    Ui::CloudDiskWindow* ui;

protected slots:
    void enableObjBtn(bool);
};

#endif // CLOUDDISKWINDOW_H

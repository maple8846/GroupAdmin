# GroupAdmin
用于电报群的付费社群管理

环境要求：
Linux系统，要求python3.8以上版本，已经安装mariadb，如果没安装参考下面安装。


不建议使用国内云服务提供商，如阿里，腾讯等，涉及电报，数字货币服务器可能会被封禁。推荐vultr购买服务器，一个月最低10美元左右，支持支付宝付款。
https://www.vultr.com/?ref=9446732


centos系统按顺序执行如下命令安装：
sudo yum update
sudo yum install mariadb-server mariadb
sudo systemctl start mariadb

ubuntu系统使用按顺序执行如下命令安装：
sudo apt update
sudo apt install mariadb-server
sudo systemctl start mariadb

准备完毕后，将所有问下放在同一目录下。

首先，设置配置文件config.txt。主要设置bottoken，chat_id，nowpaymentsapi，price四个文件，把他们设置成你自己的就ok

bottoken是电报机器人的token，用来控制机器人

chat_id是被机器人管理的群的id，机器人只有知道群的id以后才能对其进行管理。

nowpaymentsapi是用来进行收款的第三方支付api，实现收款成功后的通知，可以通过如下链接注册获取。
https://nowpayments.io/?link_id=2778376314

price是入群费用，第一版只支持按年付费，计价单位美元，直接填入数字即可。例如price:99 即一年99美元。用户采用USDT付款，由于usdt对美元存在实时汇率波动，实际支付金额不是准确的99USDT，可能是98.6usdt或者其他，存在一个小偏差。

注意，配置文件中的冒号一定不能是中文冒号，必须使用英文冒号。



然后按顺序执行下面的命令
chmod +x createdb.sh  

./createdb.sh         

pip3 install -r requirements.txt

 

至此，机器人已经成功配置成功。需要使用机器人还需进行购买后使用


最终，执行如下命令启动群管理机器人
chmod +x start.sh
./start.sh  

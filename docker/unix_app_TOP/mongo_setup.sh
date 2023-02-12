 #!/bin/sh
apt-get install -y mongodb 
apt install ./mongodb-database-tools-*-100.6.0.deb
mongorestore -d test_eval ./dump/test_eval/
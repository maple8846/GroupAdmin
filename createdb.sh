CONFIG_FILE="$PWD/config.txt"
DB_NAME="usertable"
DB_PASSWORD=$(awk -F ':' '/password/ {print $2}' "$CONFIG_FILE")
DB_USER=$(awk -F ':' '/user/ {print $2}' "$CONFIG_FILE")

# Create database and grant privileges to user
mysql -e "CREATE DATABASE IF NOT EXISTS $DB_NAME;"

mysql -e "CREATE USER '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASSWORD';"
mysql -e "GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'localhost';"


# Create table
mysql "$DB_NAME" -e "CREATE TABLE IF NOT EXISTS USERTBL (
  usr_id VARCHAR(50) NOT NULL PRIMARY KEY,
  expiration_date TIMESTAMP NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
);"





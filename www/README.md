## www configuration

Not needed.

Just set the correct paths under your apache site file.

For instance:

    <VirtualHost *:80>
        DocumentRoot /home/somebody/pre.di.c/clients/www
        <Directory />
            Options FollowSymLinks
            AllowOverride None
        </Directory>
        <Directory /home/somebody/pre.di.c/clients/www/>
            Options All Indexes FollowSymLinks MultiViews
            Require all granted
            allow from all
        </Directory>
    </VirtualHost>

    Listen 8080
    <VirtualHost *:8080>
        DocumentRoot /home/somebody/simplepre/www
        <Directory />
            Options FollowSymLinks
            AllowOverride None
        </Directory>
        <Directory /home/somebody/simplepre/www/>
            Options All Indexes FollowSymLinks MultiViews
            Require all granted
            allow from all
        </Directory>
    </VirtualHost>



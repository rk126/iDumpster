iDumpster
=========

Intelligent Dumpster Sensing and Truck Routing Demo


# Dependencies

- Flask

    - sudo pip2.7 install flask

- PyYAML

    - sudo pip2.7 install PyYaml

- enum34

    - sudo pip install enum34

# Usage

    sudo python2.7 demo_web.py

Navigate web page to localhost or point it at the IP Address of the computer
that ran the above command.

    iDumpster.py [-h] -b message broker [-p virtual host]

                 [-c login:password] -k routing key -v volume -x x -y y

optional arguments:

    -h, --help            show this help message and exit

    -b message broker, --broker_address message broker

                          This is the ip address or domain of the message broker

    -p virtual host, --path virtual host

                          Path to Virtual Host to connect to on the message

                          broker.

    -c login:password, --credentials login:password

                          Credentials to use when logging in to message broker

    -k routing key, --key routing key

                          The routing key for publishing messages to the message

                          broker

    -v volume, --capacity volume

                          Volume that this trash can will hold before becoming

                          full

    -x x, --locx x        Fake location of the dumpster on x axis

    -y y, --locy y        Fake location of the dumpster on y axis


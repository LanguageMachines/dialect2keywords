[![Language Machines Badge](http://applejack.science.ru.nl/lamabadge.php/LaMachine)](http://applejack.science.ru.nl/languagemachines/)
[![Python 3.6.9](https://img.shields.io/badge/python-3.6.9-blue.svg)](https://www.python.org/downloads/release/python-369/)

Dialect2keyword
===============

This webinterface is designed to convert words in Dutch dialects ("dialectopgaven") into standard Dutch keywords ("vernederlandste trefwoorden") which can be used as the basis for interoperable searches through various dialect dictionaries.

You can upload a list of Dutch dialect words (UTF8-format). These will be automatically converted to suggestions for keywords. This may take a while, but the tool will send you an email when it is done. After that the tool will display a couple of suggestions for keywords, from which you can select the correct one. Alternatively you can copy the closest one, and correct it manually. When you are done you can download the result as a text file..

Installation
------------

This project is developed within the [LaMachine](https://github.com/proycon/LaMachine) virtual environment. If used within LaMachine, requires no package installation. The dependencies are the following:

*   [Python (3.6.9)](https://www.python.org/downloads/release/python-369/)
*   [Django (3.1.1)](https://github.com/django/django)
*   [Phonetisaurus](https://github.com/AdolfVonKleist/Phonetisaurus)
*   [python-Levenshtein (0.12.0)](https://github.com/miohtama/python-Levenshtein)

You can clone this repository to your machine with the following code:

  ```
  $   git clone https://github.com/LanguageMachines/dialect2keywords.git
  ```

Running
-------

1.  Activate your virtual environment. For activation of LaMachine environments, please consult [LaMachine Usage Documentation](https://github.com/proycon/LaMachine#usage).

1.  Before running the program, you need to set the following environment variables each time.

    *   `SECRET_KEY`: Random string value
    *   `EMAIL_HOST`: Email service host
    *   `EMAIL_PORT`: Email service connection port
    *   `EMAIL_HOST_USER`: Sender email address
    *   `EMAIL_HOST_PASSWORD`: Sender email password

    Please consult to [Django Cryptographic Signing](https://docs.djangoproject.com/en/3.1/topics/signing/) and [Sending Emails with Django](https://docs.djangoproject.com/en/3.1/topics/email/#smtp-backend) documentations to have a better understanding on them.

    An example code for setting these variables:

    ```
    $   export EMAIL_HOST_USER='< insert the custom value required >'
    ```

1.  Go to the main directory of the repository:

    ```
    $  cd /path/to/the/repository/dialect2keyword/
    ```

1.  Run the Django server on a specific port number. In the below example, you need to replace the `PORT` variable with a 4-digit number. If not given at all, default port number is set to `8000`. For further information consult to [Django Runserver Documentation](https://docs.djangoproject.com/en/3.1/ref/django-admin/#runserver).

    ```
    $  python manage.py runserver PORT
    Example:
    $  python manage.py runserver 7658
    ```

1.  If you are running the program on a remote server, and would like to reach the interface from the browser of your local machine, you can create an [SSH tunnel](https://www.ssh.com/ssh/tunneling/example) to the remote server. If there is no domain name configured for the remote server, you can connect to the public IP address of the server.

    ```
    $  ssh -L PORT:localhost:PORT username@host.domain.name.com
    OR
    $  ssh -L PORT:localhost:PORT username@public.IP.address
    Example:
    $  ssh -L 7658:localhost:7658 jane@servers.janeandjohndoe.com
    ```

    In the above examples, `username`, `host.domain.name.com`, `public.ip.address`, and `PORT` variables needs to be replaced with actual values. `PORT` needs to be the same port number you have set while running the Django server (see the previous step).

1.  After the SHH tunneling, you can go to `localhost:PORT` on your browser to see the interface. You, again, need to replace `PORT` with the same 4-digit number which was set while running the Django server. In the case of our examples above, this would be `localhost:7658`.

Phonetisaurus Model
-------------------
**Replacing the current Phonetisaurus models**:

The Phonetisaurus model files, used by the system, are stored in the folder `models`. If you have create a new Phonetisaurus model and would like them to be used by the system, moving the new files to the `models` folder and replacing the old ones will be enough. Keeping the names of the new files the same as the old ones (as listed below) will prevent a change in the code.

*   `phonetisaurus-model.corpus`
*   `phonetisaurus-model.fst`
*   `phonetisaurus-model.o8.arpa`

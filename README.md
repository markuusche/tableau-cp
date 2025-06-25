> [!NOTE] 
> _It is expected that you cannot run this project without base url and local datas._ </br>
> _The purpose of this project is to demonstrate that I've developed something for personal use and future reference._ </br>
> _If you have any questions, feel free to contact me through one of my socials on my github profile._


<img src="https://cdn-icons-png.freepik.com/256/7178/7178515.png" width="100" />

tableau data fetcher [automation]
======
SQEOP Automation

Project Dependencies
---------------------

- `python`
- `selenium`
- `pytest`
- `pyyaml`
- `google-auth`
- `google-auth-oauthlib`
- `google-auth-httplib2`
- `google-api-python-client`
- `google-api-python-client`

Coverage
---------

   * [Data]

Pre-requisites
--------------

1. Python 3 (Make sure python is added to your system PATH)
2. Python Extension (VSCode)
3. pip
4. virtualenv
5. creds.json (you cant)
------------------------------------------------
Setting up first run on your local machine
------------------------------------------

1. Clone this project on your local machine

   ```
   https://github.com/markuusche/tableau-cp
   ```

3. Open a terminal inside your local clone of the repository.

4. Using python's virtualenv, create a virtual environment inside the project. <br>
   Install:
   ```
   pip install virtualenv
   ```
   Create a virtual environment:
   ```
   virtualenv venv
   ```

   where venv is the name of the virtual environment you are creating.
   It is also recommended to use __venv__ as the name of your virtual environment
   cause this is the recognized file exception on our ``.gitignore``

6. Activate the virtualenv you just created.
   
   * Windows CMD
      ```bash
      venv\Scripts\activate
      ```
   * Windows Git Bash
      ```bash
      source venv/scripts/activate
      ```
   * Windows Powershell
      ```bash
      venv\Scripts\activate.ps1
      ```
   * MacOS/Linux
      ```bash
     source venv/bin/activate
      ```

7. Install the project dependencies.
    ```bash
     pip install -r requirements.txt
    ```

Thats it! You have setup your local environment to run test for this project.

Run the script in visual mode (_Recommended_)
> [!IMPORTANT]
> this command already includes verbosity, stdout & stderr and quiet flags. See [pytest.ini](https://github.com/markuusche/tableau-cp/blob/main/pytest.ini)
```bash
pytest
```




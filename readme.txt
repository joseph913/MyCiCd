Before running the program please make sure that:
    - git command in path
    - docker installed and user able to run it
    - install ngrok from https://ngrok.com/ , it makes your computer accessible from the net
    - have python 3.6 or newer installed
    - install python3 dependencies from requirements.txt
    - github repo has to have Dockerfile in its root
    - give execution rights to all files that require

Usage:
    in dedicated console tab switch to dir containing my_cicd.py and run
    ./my_cicd.py github-repo-url-to-watch your-github-access-token

    running with login:passwd wasn't implemented since wasn't a requirement and due to time shortage

Use case:
    As a developer I want to keep track on changes in repository without any effort. So I fire up
    ./my_cicd.py in dedicated console tab and can be sure, that targeted app in docker container is
    up to date.

Notes:
    - originally I thought of simple socket server but it was reasonable to use out of the box
      solution which is pyramid web framework in this case
    - ngrok was used as a fast solution to provide an url and forward port to the outer net
    - it this case I assumed no control over Dockerfile in the repo being observed. Keeping in mind
      that the Dockerfile can be changed on any commit led me to rebuild image and container on
      every push event. Otherwise the're better ways to update container's content like using
      binds or volumes if possible

Disclaimer - I totally understand that having two processes - ngrok and the utility itself - is a
redundancy, but as proof of concept considered acceptable. Original version was started on simple
web sockets but parsing request/response and forwarding port outside was time consuming.

# Create a Slack bot using Django: Part I

TODO: Course outline with current part bolded?

## Objectives

* Setup a bot development environment.
* Create a bot called `@timebot`. This bot will support one slash command, `/time`, which will return the current UTC time.

## Prerequisites

* A basic working knowledge of Django and Django Rest Framework.
* Install Docker and [Cookiecutter](https://github.com/audreyr/cookiecutter).

## Architecture

Before we start, let's sketch what our high level architecture looks like:

TODO: PUT PHOTO HERE

On the left, we have our local, development server. This server will run our Django code and expose a REST API.

In the middle, we have a service that creates a tunnel to our local server. This is helpful because when Slack needs to respond to a query of ours, it must respond by sending a HTTP POST to a secure (https) URL under our control. So why don't we tell Slack to POST directly to the public IP of our local server? Several reasons including we might have a dynamically assigned IP (which means we would need to annoying change the configuration every so ofen), we might be behind a firewall, and/or we don't have a SSL certificate on hand. So we rely on an intermediate tunneling service, [ngrok](https://ngrok.com/), that creates a secure and publically accessible URL for us that we configure in Slack (more on this part later). Whatever it receives from Slack gets routed to us. Whatever we send to it will get passed on to Slack.

On the right, we have Slack. When our bot is addressed in a Slack room, Slack will send a HTTP POST to us (through ngrok). When we want to send something to Slack, we'll send a HTTP POST to Slack (again, through ngrok).

As a reminder, this archiecture is just for testing purposes as we design and develop our bot. When it comes time to deploy our bot on DigitalOcean for real users (in part II), we'll need to change it.

## Development environment

### Django

Instead of building a Django project from scratch, we'll use one from off the shelf using [Cookiecutter](https://github.com/audreyr/cookiecutter). 

Let's download a preconfigured Django 2.X project using Python 3.X with Django Rest Framework preinstalled. 

Run the command below to download the empty, preconfigured Django project. Hit return for every prompt or else later commands will not work.

`cookiecutter gh:agconti/cookiecutter-django-rest`

Run the command below to build and start the Docker container:

`docker-compose up`

Do a quick test to ensure your container is working correctly. Run the command below and verify that you receive a readable response:

`curl -d '{"username":"'"$RANDOM"'"email":"test@test.com", "first_name":"test", "last_name":"user"}' -H "Content-Type: application/json" -X POST http://0.0.0.0:8000/api/v1/users/ | python -m json.tool`

Make sure you have `ngrok` running too. In a separate terminal, navigate to the directory where ngrok is located and run:

`./ngrok http 8000`

Check the live output of `ngrok`. You should see a URL to the right of "Forwarding". Something like `https://random123.ngrok.io`. Copy that URL and open it in your browser. You should see a Django Rest Framework page. 

Take a second to understand what just happened: we spun up a local Django server and then ran `ngrok` to expose our local server to the wide web. That ngrok'd URL can be accessed by anyone---including Slack. 

### Slack

Now that we have our local development environment setup, let's configure Slack to talk to us.

If you haven't already, [create a Slack workspace](https://get.slack.help/hc/en-us/articles/206845317-Create-a-Slack-workspace). This is where we will install our bot and play with it.

Now we need to create a Slack app (don't let the term 'app' throw you off here; it's how Slack categorizes bots, among other things). Go to the [Create a Slack App](https://api.slack.com/apps?new_app=1) page and create an app like so (your workspace name may be different):

TODO: INSERT SCREENSHOT

Next, we need to apply permission scopes to our app. These specify what our bot is and is not allowed to do. Slack requires atleast one scope be applied to our app. In our case, we just want it to send messages. Under the **Features** section, find the **OAuth & Permissions** button on the navigation menu:

TODO: INSERT SCREENSHOT

Scroll down to the **Scopes** section and add the `chat:write:bot` scope like so:

TODO: INSERT SCREENSHOT

We're almost there. We still need to install this app to our workspace. Under the **Settings** section, find the **Install App** button on the navigation menu:

TODO: INSERT SCREENSHOT

Click the "Install App to Workspace" button and then click "Authorize" on the subsequent page. Your Slack app and Slack workspace are now connected.

Now, we need to configure our Slack app to support the slash command we want to run. This is an design decision Slack made: all slash commands must be predefined in the Slack app. In order to comply, let's look inside the **Features** section and find the ***Slash Commands** section:

TODO: INSERT SCREENSHOT

Click on "Create New Command" and fill out the form like so:

```
Command: /time
Request URL: <YOUR_NGROK_URL>/api/v1/bot/slashcommand/
Short descripton: Show the current time in UTC.
```

Note the request URL; this is the endpoint Slack will POST to. 

Flip over to your workspace and type `/time`. Slack should show a hint like below. If it doesn't, refresh your workspace. 

TODO: INSERT SCREENSHOT

Run the command in Slack. Uh oh. Wait. Do you see what I see?

TODO INSERT SS

Hrm. Let's flip over to our `ngrok` terminal:

TODO INSERT SS

Whoa, cool! Slack reached out to us with a POST request. However, looks like it got a `404` error from us:

TODO: INSERT SCREENSHOT

That's OK, though! This is actually expected! We know the `/api/v1/users/` endpoint works but we haven't implemented the `/api/v1/bot/slashcommand/` endpoint. So Slack tried to reach out to us and we simply weren't ready. <MAYBE PHOTO SHOWING ARCH DIAGRAM MALFUNCTIONING HERE?> Let's pause and celebrate what we've accomplished:

**We now have an end-to-end connection setup between our local development environment and Slack.**

## Slash Command

Now that our infrastructure is in place, let's adjust our Django server to properly respond to Slack's POST requests.

Right now, our Django project only has one app, `users`. Because we're creating a Slack bot that prints out the time, the existing `users` app may not be the best place for it. Let's create another app called `bot` and put all Slack bot related code in there.

Let's SSH into our Docker container:

`docker exec -it piedpiperweb_web_1 /bin/bash
`

And create the Django app:

```
mkdir piedpiper/bot
python manage.py startapp bot piedpiper/bot/
```

Let's adjust our Django project settings so that the 



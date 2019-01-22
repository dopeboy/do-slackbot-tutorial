# Create a Slack bot using Django: Part I

TODO: Course outline with current part bolded?

## Objectives

* Setup a bot development environment.
* Create a bot called `@timebot`. This bot will support one slash command, `/time`, which will return the current UTC time.

## Prerequisites

* A basic working knowledge of Django and Django Rest Framework.
* Install Docker and [Cookiecutter](https://github.com/audreyr/cookiecutter).
* Download [ngrok](https://ngrok.com/download)

## Architecture

Before we start, let's sketch what our high level architecture looks like:

TODO: PUT PHOTO HERE

On the left, we have our local, development server. This server will run our Django code and expose a REST API.

In the middle, we have a service that creates a tunnel to our local server. This is helpful because when Slack needs to respond to a query of ours, it must respond by sending a HTTP POST to a secure (https) URL under our control. So why don't we tell Slack to POST directly to the public IP of our local server? Several reasons including we might have a dynamically assigned IP (which means we would need to annoyingly change the configuration every so ofen), we might be behind a firewall, and/or we don't have a SSL certificate on hand. So we rely on an intermediate tunneling service, [ngrok](https://ngrok.com/), that creates a secure and publically accessible URL for us that we configure in Slack (more on this part later). Whatever it receives from Slack gets routed to us. Whatever we send to it will get passed on to Slack.

On the right, we have Slack. When our bot is addressed in a Slack room, Slack will send a HTTP POST to us (through ngrok). When we want to send something to Slack, we'll send a HTTP POST to Slack (again, through ngrok).

As a reminder, this archiecture is just for testing purposes as we design and develop our bot. When it comes time to deploy our bot on DigitalOcean for real users (in part II), we'll need to change it.

## Development environment

### Django

Instead of building a Django project from scratch, we'll use one from off the shelf using [Cookiecutter](https://github.com/audreyr/cookiecutter). Let's download a preconfigured Django 2.X project using Python 3.X with Django Rest Framework preinstalled. Run the command below to download the project. Hit return for every prompt to accept defaults or else later commands will not work.

`cookiecutter gh:agconti/cookiecutter-django-rest`

Run the command below to build and start the Docker container:

`docker-compose up`

Do a quick test to ensure your container is working correctly. Run the command below and verify that you receive a readable response:

`curl -d '{"username":"'"$RANDOM"'"email":"test@test.com", "first_name":"test", "last_name":"user"}' -H "Content-Type: application/json" -X POST http://0.0.0.0:8000/api/v1/users/ | python -m json.tool`

Make sure you have `ngrok` running too. In a separate terminal, navigate to the directory where ngrok is located and run:

`./ngrok http 8000`

Check the live output of `ngrok`. You should see a URL to the right of "Forwarding". Something like `https://random123.ngrok.io`. Copy that URL and open it in your browser. You should see a Django Rest Framework page. 

Let's take a second to understand what just happened: we spun up a local Django server and then ran `ngrok` to expose our local server to the wide web. That ngrok'd URL can be accessed by anyone---including Slack. 

### Slack

Now that we have our local development environment setup, let's configure Slack to talk to us.

If you haven't already, [create a Slack workspace](https://get.slack.help/hc/en-us/articles/206845317-Create-a-Slack-workspace). This is where we will install our bot and play with it.

Next, we need to create a Slack app (don't let the term 'app' throw you off here; it's how Slack categorizes bots, among other things). Go to the [Create a Slack App](https://api.slack.com/apps?new_app=1) page and create an app like so (your workspace name may be different):

TODO: INSERT SCREENSHOT

Next, we need to apply permission scopes to our app. These specify what our bot is and is not allowed to do. Slack requires atleast one scope be applied to our app. In our case, we just want our bot to send messages. Under the **Features** section, find the **OAuth & Permissions** button on the navigation menu:

TODO: INSERT SCREENSHOT

Scroll down to the **Scopes** section and add the `chat:write:bot` scope like so:

TODO: INSERT SCREENSHOT

We're almost there. We still need to install this app to our workspace. Under the **Settings** section, find the **Install App** button on the navigation menu:

TODO: INSERT SCREENSHOT

Click the "Install App to Workspace" button and then click "Authorize" on the subsequent page. Your Slack app and Slack workspace are now connected.

Now, we need to configure our Slack app to support the slash command we want to run. This is a design decision Slack made: all slash commands must be predefined in the Slack app. In order to comply, let's look inside the **Features** section and find the ***Slash Commands** section:

TODO: INSERT SCREENSHOT

Click on "Create New Command" and fill out the form like so:

```
Command: /time
Request URL: <YOUR_HTTPS_NGROK_URL>/api/v1/bot/slashcommand/
Short descripton: Show the current time in UTC.
```

Note the request URL; this is the endpoint Slack will POST to when someone runs the slash command.

Flip over to your workspace and type `/time`. Slack should show a hint like below. If it doesn't, refresh your workspace. 

TODO: INSERT SCREENSHOT

Now, run the command in Slack. Uh oh. Wait. Do you see what I see?

TODO INSERT SS

Hrm. Let's flip over to our `ngrok` terminal:

TODO INSERT SS

Whoa, cool! Slack reached out to us with a POST request. However, looks like it got a `404` error from us:

TODO: INSERT SCREENSHOT

That's OK, though! This is actually expected. We know the `/api/v1/users/` endpoint works but we haven't implemented the `/api/v1/bot/slashcommand/` endpoint. So Slack tried to reach out to us and we simply weren't ready. <MAYBE PHOTO SHOWING ARCH DIAGRAM MALFUNCTIONING HERE?> Let's pause and celebrate what we've accomplished though:

**We now have an end-to-end connection setup between our local development environment and Slack.**

## Application code

Now that our infrastructure is in place, let's adjust our Django server to properly respond to Slack's POST requests.

Right now, our Django project only has one app, `users`. Because we're creating a Slack bot that prints out the time, the existing `users` app may not be the best place for it. Let's create another app called `bot` and put all Slack bot related code in there.

Let's SSH into our Docker container:

`docker exec -it piedpiper-web_web_1 /bin/bash
`

And create the Django app:

```
mkdir piedpiper/bot
python manage.py startapp bot piedpiper/bot/
```

Let's adjust our Django project settings so that it sees our new app. Open `piedpiper/config/common.py` and make the following edit:

```
...
INSTALLED_APPS = (
    ...
    'piedpiper.users',
    'piedpiper.bot' # Add this
)
...
```

Before we think about replying to Slack's POST request, let's take a look at what they send us. Open `piedpiper/bot/views.py` and replace its contents with the following:

```
from django.conf import settings
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
    
import json                    
      
        
class SlackSlashCommandView(APIView): 
    permission_classes = (AllowAny,)
        
    def post(self, request, format=None):
        if settings.DEBUG:
            print("*** INCOMING SLASH COMMAND START ***")
            print(json.dumps(request.data, indent=4))
            print("*** INCOMING SLASH COMMAND END ***")
      
        return Response(status=status.HTTP_200_OK)

```

Here, we are printing the payload attached to any POST request that comes our way. (Note - I'm using `settings.DEBUG` to determine whether to print and `print()` to perform the actual printing; you may choose to use your own logger to simplify. Also, I'm allowing _anyone_ to POST us because of the lax permissions. In part II, we'll tighten this up).

Next, let's configure our `urls.py` to take notice of our new view. In `piedpiper/urls.py`, add the following up top:

```
...
from .bot.views import SlackSlashCommandView
...

```

And replace the following line:

```
path('api/v1/', include(router.urls)),
```

with:

```
path('api/v1/', 
    include(
        router.urls +
        [path('bot/slashcommand/', SlackSlashCommandView.as_view())]
    )
), 
```

Now we're all set. Let's try running our `/time` slash command again in our Slack workspace. If all goes to plan, we should see `                                                        POST /api/v1/bot/slashcommand/ 200 OK ` in our `ngrok` logs and something similar to the following in our Django logs:

```
*** INCOMING SLASH COMMAND START ***
 {
     "token": "KhLeBTZaE60SuHh7sfNVuiyM",
     "team_id": "T54GX75QT",
     "team_domain": "dobotplayground",
     "channel_id": "C55DBQS3Y",
     "channel_name": "general",
     "user_id": "U54MRS21K",
     "user_name": "arithmetic",
     "command": "/time",
     "text": "",
     "response_url": "https://hooks.slack.com/commands/T54GX75QT/530807404486/7q6n8CGIOwf63D6Nl1vGSC2h",
     "trigger_id": "530807404518.174575243843.9bd4321ed6cce53289e95fbdb332c132"
 }
*** INCOMING SLASH COMMAND END ***
```

__Incredible.__ Check out all that data. Most of it seems self explanatory though `response_url` and `trigger_id` are a little mysterious. You'll also notice that Slack is no longer showing an error message in the workspace. It is getting a response from us now (albeit, empty) but that's enough to satisfy it.

In any case, we've verified what Slack is sending to us. Let's get back to our main task of responding to it so that our dear user, the one who issued `/time`, isn't left staring blankly at a responseless slash command.

Slack offers [two ways](https://api.slack.com/apps/AFEN3KGMT/slash-commands?saved=1) to respond to slash commands; we'll chose the 'immediate response' method. What that means is when Slack sends us a POST request, we'll respond to it with a non-empty JSON payload. 

Earlier, in our `piedpiper/bot/views.py`, we were responding like so:

```
return Response(status=status.HTTP_200_OK)
```

Let's replace that line with:

```
return Response({
        "text": "Time to get a watch!"
    },
    status=status.HTTP_200_OK
)
```

And now, when we rerun the slash command, we should see the following in our Slack workspace:

TODO - INSERT PHOTO

Amazing! Our local development server successfully responded to a slash command from Slack. We're returning a static string, which is great and all, but let's return the current UTC time. In our `views.py`, we'll need to import `datetime` up top and also adjust our `return` statement like so:

```
...
from datetime import datetime
...

class SlackSlashCommandView(APIView):
    def post(...):
        ...
        return Response({
                "text": datetime.utcnow().strftime(
                    "%B %m, %Y %H:%M %p")
            },
            status=status.HTTP_200_OK
        )        
```

Which should so:

TODO - INSERT PHOTO

Tada, we're all done!
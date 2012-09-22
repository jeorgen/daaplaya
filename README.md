daaplaya
========

Daaplaya is an Mp3 player that connects to simple non-authenticating DAAP servers, such as Firefly, http://en.wikipedia.org/wiki/Firefly_Media_Server . It runs on Linux with gtk and gmediastreamer, it might run on other platforms such as Windows if you install or bundle gtk and such.

## Rationale
Over the last two years I have had big problems getting either the Rhythmbox or the Banshee Mp3 players to connect reliably to my Firefly DAAP servers on the local network. These problems have held fast across several versions of Ubuntu. Eventually I gave up, verified that the python libraries for service discovery and DAAP communication had no problems, and wrote my own Mp3 player for DAAP servers, Daaplaya, and I now run that in lieu of Rhythmbox and Banshee on my Ubuntu machines. It uses the gstreamer library for sound playback.

## Limitations
This project has only been developed to the point where it "works for me". It does not handle authentication and would not work with, as far as I understand, Apple's servers. It works with the Firefly DAAP server though.

The user interface is barebones and you cannot do any searches or filtering. Daap allows several databases per server, daaplaya will only use the first one per server. Daaplaya can only see playlists not files, however Firefly does make a playlist with all files in so in practice that is not a problem. It is advised to make dedicated playlists for any subsets you would like to play.

## Requirements

It requires a couple of python libraries, see the beginning of the daaplaya.py file or just run it and install python libraries until it stops complaining. It needs gtk and avahi among others. Sorry about not being more specific.


## How to use it

Have DAAP servers on your local network, preferably Firefly.

start it with

python daaplaya.py

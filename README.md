# Docker-powered microservice network for a more interactive cross-platform livestream.
My custom livestream environment built [live on stream](https://twitch.tv/mitchsworkshop).
This project is a (mostly) scratch-built network of microservices used both to store and
analyze stream data and to build a more interactive, cross-platform livestream.
All services run in Docker and are written entirely in Python.

## Requirements
This project runs on a Docker Compose network. To run it, all you will need is 
[Docker Compose](https://docs.docker.com/compose/install/) `version 1.29+`.

## Starting the network
To run the project:
- Nagivate to the directory where `docker-compose.yml` is stored.
- Run `docker-compose up -d --build`
- Check the service logs with `docker-compose logs -f` to verify that everything is running.

## Upcoming services
The [Miro board](https://miro.com/app/board/o9J_l0QVd1o=/) is an evolving document that
shows every service that will be added to this repository. Currently, all are written in
Python and there are no immediate plans to change that.

## Join the conversation
If you want to hang out with a few hundred of us and talk about this project, or anything
at all that you want to talk about, [join the Discord server]() and come be nerds together.
And of course, if you want to talk with me in real-time, the best place to do that is on
the [livestream that this project is powering](https://twitch.tv/mitchsworkshop).

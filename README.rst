termiteOS
=========

.. image:: https://travis-ci.org/nachoplus/termiteOS.svg
   :target: https://travis-ci.org/nachoplus/termiteOS

A telescope Operating System base on zmq and Protocol Buffers. Documentation https://nachoplus.github.io/termiteOS/index.html
   

Introduction
------------
Termite OS is a modular, adaptable, easily extendable telescope operating system developed primarily, but not exclusively, in python. 

It wants to answer to several limitations that most of the commercial mount controllers have. It wants to be a platform where you can incorporate all kinds of functionalities that the professional or amateur astronomer may need in a simple way.

Posible use case:

- To motorize a DIY mount or retrofit a old one.
- Make your telescope be able to track the ISS or any other satellite.
- Implement new protocol commands.
- New native protocols, i.e. indilib
- Control over the objects catalogs built into your telescope.
- Integrate pointing model in your mount.
- Connect a GPS to your mount and use his data for location and time.
- Define the horizon of your observatory.
- WiFi or Bluetooth access to your mount
- Develope new motion estrategies.

With termiteOS you will address all this things and more.


Termite OS is a **work in progress** but much of the functionality is already available:

- Stepper controller using Raspberry PI and the integrated DRV8825 widely used in the 3D printer world
- LX200 command set
- Slew and celestial track
- Satellite tracking

Ongoing funtionality:

- Arduino base hardware
- BLDC motors
- Servo motors
- Web interface
- Constellation pointing


Architecture
-------------

Each termiteOS functionality is implemented as a separate program called a'node'. The nodes communicate  each other using the zmq protocol. The organization between the nodes is hierarchical thus a node can have several children but has only one parent or none in the case of the'root node'.

ZMQ (http://zeromq.org/) is used for transport and on https://developers.google.com/protocol-buffers/ for message definitions and serialization.

Each node has its own ZMQ port and a set of commands and responds to through that port. Each node opens connections with its parent node and with all its children so that messages can be exchanged.

These nodes can run on the same or different CPUs taking advantage of all the features of the ZMQ protocol.


License
-------
GPL3 
Copyright (c) July 2018 Nacho Mas

Logo made with https://www.designevo.com/en/ DesignEvo


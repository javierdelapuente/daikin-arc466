daikin-arc466
###########

This repository is not related to Daikin by any means.

The goal is to be able to imitate the remote control ARC466A6 to implement your own smart home.


I based the protocol on the following pages:
 - http://rdlab.cdmt.vn/project-2013/daikin-ir-protocol
 - http://www.mcmajan.com/mcmajanwpr/blog/2013/10/21/ir-daikin-decodificare-protocolli-infrarossi-complessi/

I use a Broadlink Mini RM3, so I thank to the authors of the fantastic library https://github.com/mjg59/python-broadlink


Installation
============



Functions Implemented
=====================

I have not tested anything related to timers, so I am pretty sure it does not work.

It should power on, power off, set temperature, set fan speed and most of the commands.

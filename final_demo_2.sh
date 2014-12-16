#!/bin/sh
#test_script.sh
#script to automate the testing of iDumpster

xterm -e python truck_program.py -b netapps.ece.vt.edu -p sandbox -c ECE4564-Fall2014:13ac0N! -tc 100 -fc 1000 -ff 1000 -x 1 -y 1 -k truck2 &

xterm -e python iDumpster_simulated.py -b netapps.ece.vt.edu -p sandbox -c ECE4564-Fall2014:13ac0N! -x 7 -y 9 -v 50 -k dumpster2 &

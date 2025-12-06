#!/bin/bash
FIFO=/tmp/live_capture.pcap

# Remove old FIFO
[ -p $FIFO ] && rm $FIFO

# Create fresh FIFO
mkfifo $FIFO
echo "FIFO criada em $FIFO"

# Launch Wireshark
wireshark -k -i $FIFO &
echo "Wireshark aberto. Correr flowchart no GRC."

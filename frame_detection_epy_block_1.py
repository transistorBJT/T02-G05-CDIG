"""
Embedded Python Blocks:

Each time this file is saved, GRC will instantiate the first class it finds
to get ports and parameters of your block. The arguments to __init__  will
be the parameters. All of them are required to have default values!
"""


import pmt
from gnuradio import gr
import threading
import time

class blk(gr.basic_block):
    """
    Channel Hopper 2.4 GHz
    - Varre canais 1–13 (2412–2472 MHz)
    - Espera 200ms por canal
    - Pára imediatamente quando recebe "found"
    """

    def __init__(self):
        gr.basic_block.__init__(
            self,
            name="Channel Hopper",
            in_sig=None,
            out_sig=None,
        )

        # Frequências 2.4 GHz
        self.freqs = [
            2412e6, 2417e6, 2422e6, 2427e6,
            2432e6, 2437e6, 2442e6, 2447e6,
            2452e6, 2457e6, 2462e6, 2467e6,
            2472e6
        ]

        self.index = 0
        self.state = "SCANNING"
        self.dwell = 0.2   # 200ms
        self.timer = None

        # Mensagens
        self.message_port_register_in(pmt.intern("found"))
        self.set_msg_handler(pmt.intern("found"), self.handle_found)
        self.message_port_register_out(pmt.intern("freq"))

    ####################################################
    # Start / Stop controlados corretamente
    ####################################################

    def start(self):
        """Chamado automaticamente quando a FG começa."""
        self.state = "SCANNING"
        self.index = 0
        self.schedule_next()
        return super().start()

    def stop(self):
        """Chamado quando a FG termina."""
        if self.timer is not None:
            self.timer.cancel()
        return super().stop()

    ####################################################
    # Hopping Timer
    ####################################################

    def schedule_next(self):
        if self.state == "SCANNING":
            self.timer = threading.Timer(self.dwell, self.hop_once)
            self.timer.start()

    def hop_once(self):
        if self.state != "SCANNING":
            return

        freq = self.freqs[self.index]
        ch = self.index + 1
        print(f"[Hopper] Switching to {freq/1e6:.1f} MHz (CH {ch})")

        # Enviar freq ao Pluto
        self.message_port_pub(
            pmt.intern("freq"),
            pmt.from_double(freq)
        )

        # Próximo canal
        self.index = (self.index + 1) % len(self.freqs)

        # Marcar novo salto
        self.schedule_next()

    ####################################################
    # Tratamento do SSID encontrado
    ####################################################

    def handle_found(self, msg):
        if self.state == "LOCKED":
            return

        self.state = "LOCKED"

        # Cancelar timer pendente
        if self.timer is not None:
            self.timer.cancel()

        locked_freq = self.freqs[self.index - 1]
        locked_ch = self.index

        print(f"[Hopper] SSID encontrado. Parado no canal {locked_ch} ({locked_freq/1e6:.1f} MHz)")

        # Garantir freq final
        self.message_port_pub(
            pmt.intern("freq"),
            pmt.from_double(locked_freq)
        )


"""
Embedded Python Blocks:

Each time this file is saved, GRC will instantiate the first class it finds
to get ports and parameters of your block. The arguments to __init__  will
be the parameters. All of them are required to have default values!
"""

import pmt
from gnuradio import gr

class blk(gr.basic_block):
    """
    SSID Detector Block
    Recebe PDUs do WiFi Parse MAC e procura um SSID específico
    """

    def __init__(self, target_ssid="MyNetwork"):
        gr.basic_block.__init__(
            self,
            name="SSID Detector",
            in_sig=None,
            out_sig=None,
        )

        self.target_ssid = target_ssid

        # Porta de entrada: recebe PDUs do WiFi Parse MAC
        self.message_port_register_in(pmt.intern("in"))
        self.set_msg_handler(pmt.intern("in"), self.handle_msg)

        # Porta de saída: emite mensagem "found" quando encontra o SSID
        self.message_port_register_out(pmt.intern("found"))

    def handle_msg(self, msg):
        """
        msg é um PDU: (metadata, u8vector payload)
        """

        meta = pmt.car(msg)
        body = pmt.cdr(msg)

        if not pmt.is_u8vector(body):
            return

        frame = bytes(pmt.u8vector_elements(body))

        # Os management frames (e beacons) têm pelo menos 36 bytes
        if len(frame) < 36:
            return

        # Frame Control
        fc = frame[0]
        type_val = (fc >> 2) & 0x03
        subtype_val = (fc >> 4) & 0x0F

        # Só queremos Management frames
        if type_val != 0:
            return

        # Beacon (subtype 8) ou Probe Response (subtype 5)
        if subtype_val not in [8, 5]:
            return

        # Management frames têm 12 bytes de "fixed parameters" após cabeçalhos
        # IEs começam normalmente em offset 36
        ie_offset = 36
        i = ie_offset

        while i < len(frame) - 2:
            element_id = frame[i]
            length = frame[i + 1]

            if i + 2 + length > len(frame):
                return  # IE inconsistente → abortar

            # SSID IE → Element ID = 0
            if element_id == 0:
                ssid_bytes = frame[i + 2 : i + 2 + length]
                try:
                    ssid = ssid_bytes.decode(errors="ignore")
                except:
                    ssid = ""

                if ssid == self.target_ssid:
                    print(f"[SSID Detector] SSID encontrado: '{ssid}'")
                    # Enviar aviso (mensagem vazia tipo PMT_T)
                    self.message_port_pub(pmt.intern("found"), pmt.PMT_T)

                return  # Encontrado ou não, sair do bloco

            # Avançar para o próximo IE
            i += 2 + length


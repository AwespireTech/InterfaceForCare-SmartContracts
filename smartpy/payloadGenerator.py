import smartpy as sp

MetadataUrl = "ipfs://bafkreihaqo6lnw7wfkm3uvi3bfkztpfznqowalg7opb345ihwpl2dqcgzq"

class PayloadGenerator(sp.Contract):
    def __init__(self, string_to_bytes, nat_to_bytes_string):
        self.init(
            string_to_bytes = string_to_bytes,
            nat_to_bytes_string = nat_to_bytes_string,
            metadata = sp.utils.metadata_of_url(MetadataUrl)
        )

    @sp.onchain_view()
    def gen_payload(self, params):
        sp.set_type(params, sp.TBytes)

        result = sp.local("result", sp.bytes("0x0501"))
        
        x = sp.local("x", sp.len(params)*2)
        paddedBytesLength = sp.local("paddedBytesLength", [])
        with sp.if_(x.value == 0):
            paddedBytesLength.value.push('0')
        with sp.while_(x.value > 0):
            paddedBytesLength.value.push(self.data.nat_to_bytes_string[x.value % 16])
            x.value //= 16
        with sp.while_(sp.len(paddedBytesLength.value) < 8):
            paddedBytesLength.value.push("0")
        
        sp.for offset in sp.range(0, sp.len(sp.concat(paddedBytesLength.value)), 2):
            result.value += self.data.string_to_bytes[sp.slice(sp.concat(paddedBytesLength.value), offset, 2).open_some()]
        
        result.value += params
        
        sp.result(result.value)

# Tests
@sp.add_test(name = "Signing Payload Generator")
def test():
    scenario = sp.test_scenario()
    scenario.h1("Signing Payload Generator")

    string_to_bytes = sp.big_map(
        tkey = sp.TString,
        tvalue = sp.TBytes,
        l = {
            "00": sp.bytes('0x00'), "01": sp.bytes('0x01'),
            "02": sp.bytes('0x02'), "03": sp.bytes('0x03'),
            "04": sp.bytes('0x04'), "05": sp.bytes('0x05'),
            "06": sp.bytes('0x06'), "07": sp.bytes('0x07'),
            "08": sp.bytes('0x08'), "09": sp.bytes('0x09'),
            "0a": sp.bytes('0x0a'), "0b": sp.bytes('0x0b'),
            "0c": sp.bytes('0x0c'), "0d": sp.bytes('0x0d'),
            "0e": sp.bytes('0x0e'), "0f": sp.bytes('0x0f'),
            "10": sp.bytes('0x10'), "11": sp.bytes('0x11'),
            "12": sp.bytes('0x12'), "13": sp.bytes('0x13'),
            "14": sp.bytes('0x14'), "15": sp.bytes('0x15'),
            "16": sp.bytes('0x16'), "17": sp.bytes('0x17'),
            "18": sp.bytes('0x18'), "19": sp.bytes('0x19'),
            "1a": sp.bytes('0x1a'), "1b": sp.bytes('0x1b'),
            "1c": sp.bytes('0x1c'), "1d": sp.bytes('0x1d'),
            "1e": sp.bytes('0x1e'), "1f": sp.bytes('0x1f'),
            "20": sp.bytes('0x20'), "21": sp.bytes('0x21'),
            "22": sp.bytes('0x22'), "23": sp.bytes('0x23'),
            "24": sp.bytes('0x24'), "25": sp.bytes('0x25'),
            "26": sp.bytes('0x26'), "27": sp.bytes('0x27'),
            "28": sp.bytes('0x28'), "29": sp.bytes('0x29'),
            "2a": sp.bytes('0x2a'), "2b": sp.bytes('0x2b'),
            "2c": sp.bytes('0x2c'), "2d": sp.bytes('0x2d'),
            "2e": sp.bytes('0x2e'), "2f": sp.bytes('0x2f'),
            "30": sp.bytes('0x30'), "31": sp.bytes('0x31'),
            "32": sp.bytes('0x32'), "33": sp.bytes('0x33'),
            "34": sp.bytes('0x34'), "35": sp.bytes('0x35'),
            "36": sp.bytes('0x36'), "37": sp.bytes('0x37'),
            "38": sp.bytes('0x38'), "39": sp.bytes('0x39'),
            "3a": sp.bytes('0x3a'), "3b": sp.bytes('0x3b'),
            "3c": sp.bytes('0x3c'), "3d": sp.bytes('0x3d'),
            "3e": sp.bytes('0x3e'), "3f": sp.bytes('0x3f'),
            "40": sp.bytes('0x40'), "41": sp.bytes('0x41'),
            "42": sp.bytes('0x42'), "43": sp.bytes('0x43'),
            "44": sp.bytes('0x44'), "45": sp.bytes('0x45'),
            "46": sp.bytes('0x46'), "47": sp.bytes('0x47'),
            "48": sp.bytes('0x48'), "49": sp.bytes('0x49'),
            "4a": sp.bytes('0x4a'), "4b": sp.bytes('0x4b'),
            "4c": sp.bytes('0x4c'), "4d": sp.bytes('0x4d'),
            "4e": sp.bytes('0x4e'), "4f": sp.bytes('0x4f'),
            "50": sp.bytes('0x50'), "51": sp.bytes('0x51'),
            "52": sp.bytes('0x52'), "53": sp.bytes('0x53'),
            "54": sp.bytes('0x54'), "55": sp.bytes('0x55'),
            "56": sp.bytes('0x56'), "57": sp.bytes('0x57'),
            "58": sp.bytes('0x58'), "59": sp.bytes('0x59'),
            "5a": sp.bytes('0x5a'), "5b": sp.bytes('0x5b'),
            "5c": sp.bytes('0x5c'), "5d": sp.bytes('0x5d'),
            "5e": sp.bytes('0x5e'), "5f": sp.bytes('0x5f'),
            "60": sp.bytes('0x60'), "61": sp.bytes('0x61'),
            "62": sp.bytes('0x62'), "63": sp.bytes('0x63'),
            "64": sp.bytes('0x64'), "65": sp.bytes('0x65'),
            "66": sp.bytes('0x66'), "67": sp.bytes('0x67'),
            "68": sp.bytes('0x68'), "69": sp.bytes('0x69'),
            "6a": sp.bytes('0x6a'), "6b": sp.bytes('0x6b'),
            "6c": sp.bytes('0x6c'), "6d": sp.bytes('0x6d'),
            "6e": sp.bytes('0x6e'), "6f": sp.bytes('0x6f'),
            "70": sp.bytes('0x70'), "71": sp.bytes('0x71'),
            "72": sp.bytes('0x72'), "73": sp.bytes('0x73'),
            "74": sp.bytes('0x74'), "75": sp.bytes('0x75'),
            "76": sp.bytes('0x76'), "77": sp.bytes('0x77'),
            "78": sp.bytes('0x78'), "79": sp.bytes('0x79'),
            "7a": sp.bytes('0x7a'), "7b": sp.bytes('0x7b'),
            "7c": sp.bytes('0x7c'), "7d": sp.bytes('0x7d'),
            "7e": sp.bytes('0x7e'), "7f": sp.bytes('0x7f'),
            "80": sp.bytes('0x80'), "81": sp.bytes('0x81'),
            "82": sp.bytes('0x82'), "83": sp.bytes('0x83'),
            "84": sp.bytes('0x84'), "85": sp.bytes('0x85'),
            "86": sp.bytes('0x86'), "87": sp.bytes('0x87'),
            "88": sp.bytes('0x88'), "89": sp.bytes('0x89'),
            "8a": sp.bytes('0x8a'), "8b": sp.bytes('0x8b'),
            "8c": sp.bytes('0x8c'), "8d": sp.bytes('0x8d'),
            "8e": sp.bytes('0x8e'), "8f": sp.bytes('0x8f'),
            "90": sp.bytes('0x90'), "91": sp.bytes('0x91'),
            "92": sp.bytes('0x92'), "93": sp.bytes('0x93'),
            "94": sp.bytes('0x94'), "95": sp.bytes('0x95'),
            "96": sp.bytes('0x96'), "97": sp.bytes('0x97'),
            "98": sp.bytes('0x98'), "99": sp.bytes('0x99'),
            "9a": sp.bytes('0x9a'), "9b": sp.bytes('0x9b'),
            "9c": sp.bytes('0x9c'), "9d": sp.bytes('0x9d'),
            "9e": sp.bytes('0x9e'), "9f": sp.bytes('0x9f'),
            "a0": sp.bytes('0xa0'), "a1": sp.bytes('0xa1'),
            "a2": sp.bytes('0xa2'), "a3": sp.bytes('0xa3'),
            "a4": sp.bytes('0xa4'), "a5": sp.bytes('0xa5'),
            "a6": sp.bytes('0xa6'), "a7": sp.bytes('0xa7'),
            "a8": sp.bytes('0xa8'), "a9": sp.bytes('0xa9'),
            "aa": sp.bytes('0xaa'), "ab": sp.bytes('0xab'),
            "ac": sp.bytes('0xac'), "ad": sp.bytes('0xad'),
            "ae": sp.bytes('0xae'), "af": sp.bytes('0xaf'),
            "b0": sp.bytes('0xb0'), "b1": sp.bytes('0xb1'),
            "b2": sp.bytes('0xb2'), "b3": sp.bytes('0xb3'),
            "b4": sp.bytes('0xb4'), "b5": sp.bytes('0xb5'),
            "b6": sp.bytes('0xb6'), "b7": sp.bytes('0xb7'),
            "b8": sp.bytes('0xb8'), "b9": sp.bytes('0xb9'),
            "ba": sp.bytes('0xba'), "bb": sp.bytes('0xbb'),
            "bc": sp.bytes('0xbc'), "bd": sp.bytes('0xbd'),
            "be": sp.bytes('0xbe'), "bf": sp.bytes('0xbf'),
            "c0": sp.bytes('0xc0'), "c1": sp.bytes('0xc1'),
            "c2": sp.bytes('0xc2'), "c3": sp.bytes('0xc3'),
            "c4": sp.bytes('0xc4'), "c5": sp.bytes('0xc5'),
            "c6": sp.bytes('0xc6'), "c7": sp.bytes('0xc7'),
            "c8": sp.bytes('0xc8'), "c9": sp.bytes('0xc9'),
            "ca": sp.bytes('0xca'), "cb": sp.bytes('0xcb'),
            "cc": sp.bytes('0xcc'), "cd": sp.bytes('0xcd'),
            "ce": sp.bytes('0xce'), "cf": sp.bytes('0xcf'),
            "d0": sp.bytes('0xd0'), "d1": sp.bytes('0xd1'),
            "d2": sp.bytes('0xd2'), "d3": sp.bytes('0xd3'),
            "d4": sp.bytes('0xd4'), "d5": sp.bytes('0xd5'),
            "d6": sp.bytes('0xd6'), "d7": sp.bytes('0xd7'),
            "d8": sp.bytes('0xd8'), "d9": sp.bytes('0xd9'),
            "da": sp.bytes('0xda'), "db": sp.bytes('0xdb'),
            "dc": sp.bytes('0xdc'), "dd": sp.bytes('0xdd'),
            "de": sp.bytes('0xde'), "df": sp.bytes('0xdf'),
            "e0": sp.bytes('0xe0'), "e1": sp.bytes('0xe1'),
            "e2": sp.bytes('0xe2'), "e3": sp.bytes('0xe3'),
            "e4": sp.bytes('0xe4'), "e5": sp.bytes('0xe5'),
            "e6": sp.bytes('0xe6'), "e7": sp.bytes('0xe7'),
            "e8": sp.bytes('0xe8'), "e9": sp.bytes('0xe9'),
            "ea": sp.bytes('0xea'), "eb": sp.bytes('0xeb'),
            "ec": sp.bytes('0xec'), "ed": sp.bytes('0xed'),
            "ee": sp.bytes('0xee'), "ef": sp.bytes('0xef'),
            "f0": sp.bytes('0xf0'), "f1": sp.bytes('0xf1'),
            "f2": sp.bytes('0xf2'), "f3": sp.bytes('0xf3'),
            "f4": sp.bytes('0xf4'), "f5": sp.bytes('0xf5'),
            "f6": sp.bytes('0xf6'), "f7": sp.bytes('0xf7'),
            "f8": sp.bytes('0xf8'), "f9": sp.bytes('0xf9'),
            "fa": sp.bytes('0xfa'), "fb": sp.bytes('0xfb'),
            "fc": sp.bytes('0xfc'), "fd": sp.bytes('0xfd'),
            "fe": sp.bytes('0xfe'), "ff": sp.bytes('0xff')
        }
    )

    nat_to_bytes_string = sp.big_map(
        tkey = sp.TNat,
        tvalue = sp.TString,
        l = {x : str(x) if x < 10 else chr(ord('a')+x-10) for x in range(0, 16)}
    )
    c1 = PayloadGenerator(string_to_bytes, nat_to_bytes_string)
    scenario += c1


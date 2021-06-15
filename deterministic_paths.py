from hashlib import sha256
import hmac
from datetime import datetime


############################################
# Helper Methods
############################################

# https://bitcoin.stackexchange.com/questions/92056/what-is-the-max-allowed-depth-for-bip32-derivation-paths
MAX_BIP32 = 2 ** 31 - 1


def encode(num, base=MAX_BIP32):
    result = []
    while num > 0:
        num, remainder = divmod(num, base)
        result.append(remainder)
    return result


def decode(encoded, base=MAX_BIP32):
    res = 0
    for cnt, r in enumerate(encoded):
        res += r * base ** cnt
    return res


# Poor test coverage
NUM, BASE = 98278243937, 34
assert decode(encode(NUM, BASE), BASE) == NUM


def get_hmac_key(xpubs):
    return sha256(" ".join(sorted(xpubs)).encode()).digest()


def calc_bip32_path_to_append(hex_string):
    as_int = int(hex_string, 16)
    # convert to 124 bits (4 depth) int:
    as_int %= 2 ** 124
    return "/".join([str(x) for x in encode(num=as_int, base=MAX_BIP32)])


############################################
# Example Useage
############################################


from buidl.descriptor import P2WSHSortedMulti
from buidl.hd import HDPublicKey

# order doesn't matter, will be sorted later
QUORUM_M = 2
key_records = [
    {
        # investx12
        "xfp_hex": "aa917e75",
        "path": "m/48h/1h/0h/2h",
        "xpub": "tpubDEZRP2dRKoGRJnR9zn6EoLouYKbYyjFsxywgG7wMQwCDVkwNvoLhcX1rTQipYajmTAF82kJoKDiNCgD4wUPahACE7n1trMSm7QS8B3S1fdy",
        "account_index": 0,
        "to_blind": False,
    },
    # sell x12
    {
        "xfp_hex": "2553c4b8",
        "path": "m/48h/1h/0h/2h",
        "xpub": "tpubDEiNuxUt4pKjKk7khdv9jfcS92R1WQD6Z3dwjyMFrYj2iMrYbk3xB5kjg6kL4P8SoWsQHpd378RCTrM7fsw4chnJKhE2kfbfc4BCPkVh6g9",
        "account_index": 0,
        "to_blind": True,
    },
    # include x12
    {
        "xfp_hex": "a24ef017",
        "path": "m/48h/1h/0h/2h",
        "xpub": "tpubDFQytwvHVwxrJdKpLT1Mk2Vb8LN9qdnxYAYomKQ9akpnW32QXExbFwaPFPLXAddvmtfsVWbLEN2qEJ33RyYYEvtuhUguVnLbJhzEphhWGkm",
        "account_index": 0,
        "to_blind": True,
    },
]


def blind_key_records(key_records, quorum_m):
    # Sort key_records lexographically by xpub (needed later)
    key_records = sorted(key_records, key=lambda k: k["xpub"])

    hmac_key = get_hmac_key([kr["xpub"] for kr in key_records])

    p2wsh_sorted_multi_descriptor = f"wsh(sortedmulti({quorum_m}"
    for cnt, kr in enumerate(key_records):
        # trim leading "m/"
        starting_path = kr["path"][2:]

        if kr["to_blind"] is True:
            unique_hex = hmac.new(
                key=hmac_key, msg=str(cnt).encode(), digestmod=sha256
            ).hexdigest()
            path_to_append = calc_bip32_path_to_append(unique_hex)
            hd_pubkey_obj = HDPublicKey.parse(kr["xpub"])
            # Safety check:
            assert hd_pubkey_obj.depth == starting_path.count("/") + 1
            xpub_to_use = hd_pubkey_obj.traverse("m/" + path_to_append).xpub()
            # trim leading "m/" and append blinding path
            path_to_use = kr["path"][2:] + "/" + path_to_append
        else:
            path_to_use = starting_path
            xpub_to_use = kr["xpub"]

        p2wsh_sorted_multi_descriptor += (
            f",[{kr['xfp_hex']}/{path_to_use}]{xpub_to_use}/{kr['account_index']}/*"
        )

    p2wsh_sorted_multi_descriptor += "))"

    return p2wsh_sorted_multi_descriptor


p2wsh_sorted_multi_descriptor = blind_key_records(
    key_records=key_records, quorum_m=QUORUM_M
)
print("p2wsh_sorted_multi_descriptor:", p2wsh_sorted_multi_descriptor)

# Calc first receive addr
first_receive_addr = P2WSHSortedMulti.parse(p2wsh_sorted_multi_descriptor).get_address()
print("first_receive_addr:", first_receive_addr, "\n")


# Later, I recover all 3 seeds but didn't save my output descriptors
# I don't remember what my quorum was (1-of-3, 2-of-3, 3-of-3), nor how many/which seeds were blinded
# We try all combinations until we get recovery


def recover_output_descriptor(key_records, target_addrs, known_quorum_m=0):
    """
    The more you feed it, the more intelligent it will be about how it searches
    """
    total_tries = 0
    successful_p2wsh_descriptor = ""
    # attempt each m-of-3 option
    for quorum_m in range(1, len(key_records) + 1):

        # If a known_quorum_m is supplied, only search in that space
        if known_quorum_m and quorum_m != known_quorum_m:
            print("bail")
            continue

        # attempt blinding every possible combination of key records
        for blinding_combo_int in range(2 ** len(key_records)):

            # use binary #s to form a string like 010
            # translated to key records this means: [no_blind, yes_blind, no_blind]
            blinding_combo_str = bin(blinding_combo_int)[2:].zfill(len(key_records))

            for cnt, attempt_blind in enumerate(blinding_combo_str):
                # print("attempt_blind", attempt_blind)
                key_records[cnt]["to_blind"] = attempt_blind == "1"

            # print(f"#{quorum_m} key_records_blinding", [x["to_blind"] for x in key_records])

            total_tries += 1
            blinded_p2wsh_descriptors = blind_key_records(
                key_records=key_records, quorum_m=quorum_m
            )
            p2wsh_descriptor = P2WSHSortedMulti.parse(blinded_p2wsh_descriptors)
            for addr_cnt in range(len(target_addrs)):
                if p2wsh_descriptor.get_address(addr_cnt) in target_addrs:
                    successful_p2wsh_descriptor = blinded_p2wsh_descriptors
                    print("addr hit!")

            if False:
                if total_tries % 100 == 0:
                    print("total_tries", total_tries)

    print("total tries", total_tries)
    return successful_p2wsh_descriptor


assert recover_output_descriptor(
    key_records=key_records,
    target_addrs={"tb1q0vc3wa6fwa7uhu0xa3nt4vget5uxstd5r8jlyeynl9cfsf725v7q8l7g26"},
)


############################################
# Performance testing up to 15 seeds
############################################


from buidl.hd import HDPrivateKey

# some seed words that are valid seed phrases when repeated 12x
# https://gist.github.com/mflaxman/60c15be413c4194118eb5547ffcd15ee
seed_words = [
    "action",
    "agent",
    "aim",
    "all",
    "ankle",
    "announce",
    "audit",
    "awesome",
    "beef",
    "believe",
    "blue",
    "border",
    "brand",
    "breeze",
    "bus",
]
all_key_records = []
for seed_word in seed_words:
    hd_privkey_obj = HDPrivateKey.from_mnemonic(f"{seed_word} " * 12, testnet=True)
    path_to_use = "m/48h/1h/0h/2h"
    all_key_records.append(
        {
            "xfp_hex": hd_privkey_obj.fingerprint().hex(),
            "path": path_to_use,
            "xpub": hd_privkey_obj.traverse(path_to_use).xpub(),
            "account_index": 0,
            "to_blind": True,
        }
    )

print("#" * 88)
print(key_records)

for num_seeds in range(2, 16):
    start_time = datetime.now()

    p2wsh_sorted_multi_descriptor = blind_key_records(
        key_records=all_key_records[:num_seeds], quorum_m=num_seeds
    )
    # print("p2wsh_sorted_multi_descriptor:", p2wsh_sorted_multi_descriptor)

    # Calc first receive addr (not strictly neccesary at this step)
    first_receive_addr = P2WSHSortedMulti.parse(
        p2wsh_sorted_multi_descriptor
    ).get_address()
    # print("first_receive_addr:", first_receive_addr, "\n")

    assert recover_output_descriptor(
        key_records=all_key_records[:num_seeds], target_addrs={first_receive_addr}
    )

    print(f"{num_seeds} seeds took {datetime.now()-start_time}")

# coding=utf-8
from OpenSSL import crypto

# Whatever
ORG_NAME = "DS Productions"


def make_cert():
    # public key
    pk = crypto.PKey()
    pk.generate_key(crypto.TYPE_RSA, 4096)

    # self-signed
    cert = crypto.X509()

    cert.get_subject().O = ORG_NAME
    cert.gmtime_adj_notBefore(0)

    # 365 days of validity
    cert.gmtime_adj_notAfter(365 * 24 * 60 * 60)
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(pk)
    cert.sign(pk, "sha512")

    with open("certificate.crt", "wb") as crt:
        crt.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))

    with open("priv.key", "wb") as prv:
        prv.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, pk))

if __name__ == '__main__':
    print("Self-signed certificate generator.\n----------------------------------")

    if str(input("Do you want to proceed? y/n")).lower() == "y":
        print("Generating...")
        make_cert()
        print("Done generating self-signed certificates.")

    else:
        print("OK, quitting...")

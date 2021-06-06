## Intro

Bitcoin's multisig security model is a breakthrough in human ability to self-custody value.
By comparison, it is impossible to `3-of-5` your gold.
Multisig adoption has the power to reduce hacks/theft/loss in the bitcoin space, and give bitcoin a reputation for being the most secureable asset in human history.
This could increase adoption, as HODLers might be comfortable storing a greater percentage of their net worth in bitcoin.

There are generally three main barriers to multisig adoption:
* Additional Complexity
* Having Multiple Secure Locations
* Privacy Leakage

### Complexity

A classic addage is that "complexity is the enemy of security."
While this is true, single points of failure are also extremely dangerous.
Multisig adoption has led to more Coordinator softwares (Specter-Desktop, Caravan, Noded, Sparrow, BlueWallet, etc), Signers (Specter-DIY, Keystone/Cobo, Coldcard, BitBox02, Noded, Passport, BlueWallet, etc) guides ([example](https://btcguide.github.io/)), and collaborative custody services (Casa, Unchained, BitGo, etc).
Proper multisig allows users to make 1 (or more) catastrophic mistakes in their custody without putting funds at risk, and to configure the number of fault-tolerant failures via their `m-of-n` parameter (i.e. `3-of-5`).

There is also inherent ambiguity under current best practices.
Should each seed phrase contain the xpubs/paths of all other seed phrases?
This account map is required to validate a recieve address, but also leaks privacy (more below).
Creating an explicit [trust boundary](https://en.wikipedia.org/wiki/Trust_boundary) separates privacy information (account map) from security information (private key material, in this case BIP39 seed phrases).

### Having Multiple Secure Locations

While `4-of-7` multisig sounds great, how many people have access to `7` secure locations with around the clock security?

A scheme that enables 1 (or more) semi-trusted collaborative custodians (e.g. a lawyer, accountant, heir, close friend, "uncle Jim" bitcoiner, collaborative custody service, etc) to participate in a multisig quorum with *zero* knowledge of what they're protecting mitigates this concern (and can supply geographic/jurisdictional diversity).

Under current best-practices, a holder of a BIP39 seed phrase used in a `4-of-7` multisig wallet may be able to learn substantial information about what they're protecting.
While [multisig is strictly superior to Shamir's Secret Sharing Scheme](https://btcguide.github.io/why-multisig-advanced#shamirs-secret-sharing-scheme), having multiple seeds floating around that may convey information about what they're protecting introduces new risks (and provides a choke-point for governments to gain access to information about private holdings).

### Privacy Leakage

Standard/default BIP32 paths make it so that if a party gains unauthorized access to a BIP39 seed phrase (or even just an xpub), they may be able to learn about what funds it protects as well as the quorum required (`m-of-n`).

Under current best-practices, if a bad actor gains unauthorized access to a single seed phrase they could perhaps learn the following:
* Yesterday that seed phrase was party to a massive transaction that likely had a large change ouput (note that this situation could be true even if this seed phrase did not cosign in the transaction)
* The transaction that this seed phrase was a party to (which likely had large change sent back to itself) was a `2-of-3`, meaning that only 1 more seed phrase (along with the account map) is needed to spend funds.
* It might also be possible to know that this entity engages in similiar transactions each weekday at say 4pm local time.

_Potential outcome: show up at this person's house or place of business with a $5 wrench._

Users who instead use single-sig with a BIP39 seed words and a passphrase can make it so that anyone who finds the BIP39 seed *or* the passphrase learn nothing about what it protects.
Of course it's imortant to keep in mind that from a security perspective, loss of the BIP39 seed words *or* the passphrase means total loss of funds.

This proposal **completely eliminates** this concern.

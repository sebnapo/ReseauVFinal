# Readme groupe: NAPOLEON / BESNARD

	    Reseau ring - S6      

---> Pour lancer le programme:
Executer le fichier "mainComplete.py"

---> Pour modifier le nombre de slots:
Changer la valeur de self.initToken (par défaut à 2)
Changer la valeur de self.compteur (par défaut à 2)
Dans la couche 2 incoming:
Changer la valeur de self.compteur (par défaut à 2)
Dans la couche 2 outgoing:
Changer la valeur du if self.initToken >= (par défaut à 2)

---> Pour rajouter des MSG:
Dans le fichier mainComplete.py, rajouter les lignes:
Remplacer "X" par la source et "Y" par le destinataire
Remplacer "computer3" par computerX où X correspond au n° du PC X

# Start sending some messages from computer 'X' to computer 'Y'
    __debugOut.debugOutSource("Main",__debugOut.srcComputer,__debugOut.INFO,"Starting some message from X to Y")
    computer3.appMessageSend(destinationIdentifier="Y", numberOfMessages=1)

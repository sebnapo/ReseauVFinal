# -*- coding: utf-8 -*-
import threading
import LayerPhy
import math
import random
from Tools.DebugOut import DebugOut
import time


class NetworkStack(object):

    def __init__(self, masterHost='127.0.0.1', baseport=10000, ownIdentifier='x', autoEnter=True):
        self.__debugOut=DebugOut()
        self.__applicationList=[]
        self.__sendDelay=0
        self.__layerDelay=0
        self.__layerPhy=LayerPhy.LayerPhy(ownIdentifier, upperLayerCallbackFunction=self.layer2_incomingPDU, masterHost=masterHost, baseport=baseport, autoEnter=autoEnter)
        # You may want to change the following part
        self.__ownIdentifier=ownIdentifier
        self.outgoingPacketStack=[]
        self.outgoingPacketStackLock=threading.Lock()

        #SN TB ETAPE DE L'INITIALISATION DU TOKEN
        self.initToken = 2

        #SN TB compteur -> compteur pour le nombre de slot (couche 2)
        self.compteur = 2
        self.indice = 0
        self.paquetRecu = ""
        self.paquetAEnvoyer = "".encode("UTF-8")


    def leaveNetwork(self):
        self.__layerPhy.API_leave()

    def enableGlobalDebug(self):
        self.__layerPhy.API_subscribeDebug()

    def configureDelay(self,sendDelay=None,layerDelay=None):
        if sendDelay!=None:
            self.__sendDelay=sendDelay
        if layerDelay!=None:
            self.__layerDelay=layerDelay

    # Do not change!
    # This is the application layer protocol part: Each application has its specific port
    # The application registers a callback function that is called when a packet arrives for that particular application
    def applicationAddCallback(self, applicationPort, callBack):
        self.__applicationList.append((applicationPort, callBack))

    # Do not change!
    # The application sends packets which are stored in a buffer before being submitted
    def applicationSend(self, destination, applicationPort, pdu):
        self.outgoingPacketStackLock.acquire()
        self.outgoingPacketStack.insert(0,(destination, applicationPort,pdu))
        self.outgoingPacketStackLock.release()


#############################################################################################################################################
#############################################################################################################################################

    # Please change: This sends the first TOKEN to the ring
    # In fact, sending a TOKEN requires the creation of a new thread
    def initiateToken(self):
        self.__debugOut.debugOutLayer(self.__ownIdentifier,2,self.__debugOut.INFO,"Initiating TOKEN" )
        tokenThread=threading.Thread(target=self.application_layer_outgoingPDU, args=(True,))
        tokenThread.start()

    # Please adapt if required : This is the top layer that usually sends the data to the application
    # If pdu is None, the packet is not valid
    # forceToken determines that the return packet needs to be a TOKEN
    def application_layer_incomingPDU(self, forceToken, source, pdu):
        time.sleep(self.__layerDelay)
        self.__debugOut.debugOutLayer(self.__ownIdentifier,5,self.__debugOut.INFO,"%s: application_layer_in: received (%s) " % (self.__ownIdentifier,pdu))

        if pdu!=None:
            applicationPort=int.from_bytes(pdu[0:1],byteorder="little",signed=False)
            sdu=pdu[1:]

            # We deliver the SDU to the application that handles this message
            for (thisApplicationPort, thisApplication) in self.__applicationList:
                if thisApplicationPort==applicationPort:
                    thisApplication(source, applicationPort, sdu.decode('UTF-8'))

        # We dive back down into the network stack
        self.application_layer_outgoingPDU(forceToken)


    # Please adapt if required: This is the top layer that retrieves one element from the application layer
    def application_layer_outgoingPDU(self, forceToken=False):
        time.sleep(self.__layerDelay)
        self.outgoingPacketStackLock.acquire()

        #TB SN on compare le initToken et le ownIdentifier pour initialiser le paquet avec le computeur 'A'

        if (self.initToken != 0 and self.__ownIdentifier == 'A') or forceToken:
            destination="X"
            applicationPort=20
            sdu="TOKEN"

        else:
            if self.outgoingPacketStack != []:
                destination,applicationPort,sdu=self.outgoingPacketStack.pop()
            else :
                destination="X"
                applicationPort=20
                sdu="TOKEN"

        self.outgoingPacketStackLock.release()

        pdu=applicationPort.to_bytes(1,byteorder="little",signed=False)+sdu.encode("UTF-8")
        self.__debugOut.debugOutLayer(self.__ownIdentifier,5,self.__debugOut.INFO,"%s: application_layer_out: sending (%s) " % (self.__ownIdentifier,pdu))
        self.layer4_outgoingPDU(destination, applicationPort, pdu)


    # Please adapt!
    # Take care: The parameters of incoming (data packets arriving at the computer) and outgoing (data packets leaving from the computer)
    # should generally agree with one layer difference (i.e. here we treat the applicationPort, an identifier that knows which application
    # is asked to handle the traffic
    def layer4_incomingPDU(self, source, pdu):
        time.sleep(self.__layerDelay)
        # Let us assume that this is the layer where we determine the applicationPort
        # We also decide whether we can send immediately send a new packet or whether we need to be friendly and send a TOKEN
        # We are not friendly and send a packet if our application has one with 100% chance
        self.__debugOut.debugOutLayer(self.__ownIdentifier,4,self.__debugOut.INFO,"%s: Layer4_in: Received (%s) from %s " % (self.__ownIdentifier,pdu, source))
        self.application_layer_incomingPDU(False,source,pdu)

    # Please adapt
    def layer4_outgoingPDU(self, destination, applicationPort, pdu):
        time.sleep(self.__layerDelay)
        self.__debugOut.debugOutLayer(self.__ownIdentifier,4,self.__debugOut.INFO,"%s: Layer4_out: Sending (%s) to %s " % (self.__ownIdentifier, pdu, destination))
        self.layer3_outgoingPDU(destination, pdu)

    # Please adapt!
    # The current situation is that in this layer, the network stack takes the decision to forcibly keep the packet because it thinkgs that it is destined to this computer
    # It also authorizes immediately that a new packet can be put onto the network.
    def layer3_incomingPDU(self, interface, pdu):
        time.sleep(self.__layerDelay)

        #TB SN On va recuperer l'expéditeur et le destinaire du pdu grâce au code fournit dans les annexes

        expediteur = pdu[0:1].decode('UTF-8')
        destinataire = pdu[1:2].decode('UTF-8')

        if destinataire == 'X':
            self.__debugOut.debugOutLayer(self.__ownIdentifier,3,self.__debugOut.INFO,"%s: Layer3_in: tirage (%s) -> layer4_in\n" % (self.__ownIdentifier, pdu))
            self.layer4_incomingPDU(None,None)


        #SN TB Test pour savoir si le paquet reçus est celui qu'on à envoyer
        elif expediteur == self.__ownIdentifier:
            self.layer4_incomingPDU(None,None)

        #SN TB Test pour savoir si on est le destinaire
        elif destinataire == self.__ownIdentifier:
            print("Nice ca");
            #SN TB Si oui, on envoie à la couche 4 incoming
            self.__debugOut.debugOutLayer(self.__ownIdentifier,3,self.__debugOut.INFO,"%s: Layer3_in: tirage (%s) -> layer4_in\n" % (self.__ownIdentifier, pdu))
            self.layer4_incomingPDU(expediteur,pdu[2:])
        else:
            #SN TB Si non, on renvoie le paquet à la couche 2 outgoing pour transmettre le paquet au computer suivant
            taille = len(pdu)
            if taille < 10 :
                taille = '0'+str(taille)
            else :
                taille = str(len(pdu))
            pdu = taille.encode("UTF-8")+pdu
            self.__debugOut.debugOutLayer(self.__ownIdentifier,3,self.__debugOut.INFO,"%s: Layer3_in: tirage (%s) -> Packet to be destroyed\n" % (self.__ownIdentifier, pdu))
            self.layer2_outgoingPDU(interface,pdu)


    # Please adapt
    def layer3_outgoingPDU(self, destination, pdu):
        time.sleep(self.__layerDelay)
        # Here, we store the packet and wait until an empty token packet arrives

        #SN TB On récupère l'expéditeur et la destination, que l'on encode et ajoute au PDU
        expediteur = self.__ownIdentifier
        pdu = expediteur.encode("UTF-8")+destination.encode("UTF-8")+pdu

        #TB SN On récupère la taille et on l'ajoute au pdu
        taille = len(pdu)
        if taille < 10 :
            taille = '0'+str(taille)
        else :
            taille = str(len(pdu))
        pdu = taille.encode("UTF-8")+pdu

        self.__debugOut.debugOutLayer(self.__ownIdentifier,3,self.__debugOut.INFO,"%s: Layer3_out: Sending out (%s) via interface %d " % (self.__ownIdentifier, pdu, 0))
        self.layer2_outgoingPDU(0, pdu)

    # Please adapt
    def layer2_incomingPDU(self, interface, pdu):
        time.sleep(self.__layerDelay)
        self.__debugOut.debugOutLayer(self.__ownIdentifier,2,self.__debugOut.INFO,"%s: Layer2_in: Received (%s) on Interface %d " % (self.__ownIdentifier, pdu, interface))

        if interface == 0 : # same ring

            print(pdu)
            self.paquetRecu = pdu

            if self.compteur <= 0 :
                self.compteur = 2
                self.indice = 0
                self.paquetAEnvoyer = "".encode("UTF-8")
                #self.paquetRecu = pdu
            taille = self.paquetRecu[self.indice:self.indice+2]
            taille = int(taille.decode('UTF-8'))


            self.indice += 2
            pdu = self.paquetRecu[self.indice:self.indice+taille]
            self.indice += taille
            self.compteur -= 1


            self.__debugOut.debugOutLayer(self.__ownIdentifier,2,self.__debugOut.INFO,"%s: Layer2_in: tirage (%s) -> layer3_in\n" % (self.__ownIdentifier, pdu))
            self.layer3_incomingPDU(interface,pdu)
        else: # Another Ring, this is for routing, see later
            pass

    def layer2_outgoingPDU(self, interface, pdu):
        if self.initToken > 0 and self.__ownIdentifier == 'A' : #TB SN On regarde si on continue d'initialiser le paquet
            print('lol')
            if self.initToken >= 2 : #TB SN on est pas sur le dernier slot donc on continue d'initialiser
                self.initToken -= 1
                self.paquetAEnvoyer += pdu
                self.compteur -=1
                self.__debugOut.debugOutLayer(self.__ownIdentifier,2,self.__debugOut.INFO,"%s: Layer2_out: Sending in (%s) via interface %d " % (self.__ownIdentifier, self.paquetAEnvoyer, interface))
                self.application_layer_outgoingPDU(True)
            #TB SN On initialise le dernier slot du paquet, donc on envoie le paquet initialisé au noeud suivant
            elif self.initToken == 1:
                self.initToken -= 1
                self.paquetAEnvoyer += pdu
                self.compteur -=1
                self.__debugOut.debugOutLayer(self.__ownIdentifier,2,self.__debugOut.INFO,"%s: Layer2_out: Sending in (%s) via interface %d " % (self.__ownIdentifier, self.paquetAEnvoyer, interface))
                self.__layerPhy.API_sendData(interface, self.paquetAEnvoyer)
                #self.layer2_incomingPDU(interface,self.paquetRecu)
        #SN TB Tant que tous les slots n'ont pas été traités
        elif self.compteur > 0 :
            self.paquetAEnvoyer += pdu
            time.sleep(self.__layerDelay)
            self.__debugOut.debugOutLayer(self.__ownIdentifier,2,self.__debugOut.INFO,"%s: Layer2_out: Sending out (%s) via interface %d " % (self.__ownIdentifier, self.paquetAEnvoyer, interface))
            if self.__sendDelay!=0:
                self.__debugOut.debugOutLayer(self.__ownIdentifier,2,self.__debugOut.INFO,"%s: Layer2_out: Sleeping for %ds" % (self.__ownIdentifier,self.__sendDelay))
                time.sleep(self.__sendDelay)
            #SN TB On envoie en couche 2 incoming pour traiter le slot suivant
            self.layer2_incomingPDU(interface,self.paquetRecu)
        #SN TB tous les slots ont été traités
        else :
            self.paquetAEnvoyer += pdu
            #SN TB on envoie au noeud suivant
            self.__layerPhy.API_sendData(interface, self.paquetAEnvoyer)
 
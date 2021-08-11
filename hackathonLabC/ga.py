
#####################################################################################################################################
# Este código foi desenvolvido no escopo do evento Hackathon Lab.C - Diagnosticando Soluções, organizado pelo Critt/UFJF em 08/2021.
# O programa resolve o problema de roteamento de veículos, no contexto do serviço de coleta domiciliar de um laboratório de análises clínicas
# em sua forma básica: fornecida a matriz de distâncias entre os pontos de coleta, o AG procura pela rota de mínimo custo, considerando
# um veículo.

# O programa é escalável. É possível recodificar os cromossomos e acrescentar penalizações para incluir restrições de janela de tempo ou
# mais veículos em rota, por exemplo.

# Também é possível reescrever a importação da matriz de distâncias para construí-la a partir da API Google Distance Matrix, que calcula todas as distâncias
# a partir dos endereços fornecidos.

##############
# 0) MÓDULOS
##############

import numpy as np
import pandas as pd
import random
import operator
import os

######################
# 1) CLASSES BÁSICAS
######################

#####################################
# 1.1) Classe para o Ponto de Coleta
#####################################
class PontoColeta:
  
    # O construtor contém as coordenadas x e y da cidade
    def __init__(self, index):
        self.index = index
        
    # Devolve a distância entre dois pontos de coleta
    def distancia(self, pontoColeta):
        dist = matrizDist.loc[self.index, pontoColeta.index]
        return dist
      
#########################
# 1.2) Função de Aptidão
#########################
class Fitness:
    
    # Construtor
    # rota: sequência de pontos percorridos
    # distancia: distância total percorrida na rota
    # fitness: aptidão da rota
    def __init__(self, rota):
        self.rota = rota
        self.distancia = 0
        self.fitness = 0

    # Cálculo da distância percorrida na rota recebida
    # distAcumulada: variável acumuladora para as distância no indivíduo
    def DistanciaRota(self):
        if self.distancia == 0:
            distAcumulada = 0
            for i in range(0, len(self.rota)):
                pontoPartida = self.rota[i]
                pontoDestino = None
                if i + 1 < len(self.rota):
                    pontoDestino = self.rota[i + 1]
                else: # Se estiver no último ponto da rota, deve voltar para o ponto de partida (a matriz do laboratório).
                    pontoDestino = self.rota[0]
                distAcumulada += pontoPartida.distancia(pontoDestino)
            self.distancia = distAcumulada
        return self.distancia
    
    # Aptidão da rota: quanto maior o inverso da distância percorrida na rota, mais apta a rota.
    def rotaFitness(self):
        if self.fitness == 0:
            self.fitness = 1 / float(self.DistanciaRota())
        return self.fitness

##########################################
# 1.3) Criação da população inicial do AG
##########################################
# Cria um indivíduo a partir da aleatorização de uma lista de pontos
def GeraRota(listaPontos):
    
    rota = []
    rota.append(listaPontos[0])
    rota.extend(random.sample(listaPontos[1:], (len(listaPontos) - 1)))
    rota.append(listaPontos[0])

    return rota

# Cria uma população inicial (uma lista de rotas aleatórias)
def popInicial(popTam, listaPontos):
    populacao = []

    for i in range(0, popTam):
        populacao.append(GeraRota(listaPontos))
    return populacao

#################
# 2) RANKEAMENTO
#################
# Fez um ranking da população de acordo com a aptidão
def ranking(populacao):
    fitRotas = {} # aptidão de cada rota
    for i in range(0,len(populacao)):
        fitRotas[i] = Fitness(populacao[i]).rotaFitness() # Calcula aptidão de cada rota da população
    return sorted(fitRotas.items(), key = operator.itemgetter(1), reverse = True) # Resultados em ordem decrescente (maior aptidão primeiro)

##############
# 3) ELITISMO
##############
# Seleciona a elite e retorna os índices dos indivíduos

def elitismo(popRank, eliteTam):
    indexElite = []
    df = pd.DataFrame(np.array(popRank), columns=["Index", "Fitness"])
    df['cum_sum'] = df.Fitness.cumsum()
    df['cum_perc'] = 100 * df.cum_sum / df.Fitness.sum() # acumulado (Pareto!)

    for i in range(0, eliteTam): # Cria lista com os índices dos melhores
        indexElite.append(popRank[i][0])
    for i in range(0, len(popRank) - eliteTam):
        limite = 100 * random.random()
        for i in range(0, len(popRank)): # Dá chance para mais alguns
            if limite <= df.iat[i, 3]:
                indexElite.append(popRank[i][0])
                break
    return indexElite

###################
# 4) CROSSING-OVER
###################
#########################################
# 4.1) Formação do pool de crossing-over
#########################################
# Coloca todos os indivíduos da elite no pool
def Pool(populacao, indexElite):
    pool = []
    for i in range(0, len(indexElite)):
        index = indexElite[i]
        pool.append(populacao[index])
    return pool

#####################
# 4.2) Cruzamento
#####################
def cruzamento(pai1, pai2):
    
    filho = []
    filhoP1 = []
    filhoP1.append(pai1[0])
    filhoP2 = []
    filhoP2.append(pai2[0])
    
    geneB = geneA = 0
    
    while geneA == 0 or geneA == len(pai1):
    
        geneA = int(random.random() * len(pai1)) # escolhe o índice de uma cidade

    while geneB == 0 or geneB == len(pai2):
    
        geneB = int(random.random() * len(pai2)) # escolhe o índice de uma cidade

    startGene = min(geneA, geneB)
    endGene = max(geneA, geneB)

    for i in range(startGene, endGene):
        filhoP1.append(pai1[i])

    filhoP2 = [item for item in pai2 if item not in filhoP1]

    filho = filhoP1 + filhoP2 # concatena os dois pedaços

    filho.append(pai1[-1])

    return filho

###################################
# 4.3) Executa o crossing-over
###################################
def GeraPopCruzada(matingpool, eliteTam):
    
    filhos = []
    length = len(matingpool) - eliteTam
    pool = random.sample(matingpool, len(matingpool))

    for i in range(0, eliteTam):
        filhos.append(matingpool[i])

    for i in range(0, length):
        filho = cruzamento(pool[i], pool[len(matingpool) - i - 1])
        filhos.append(filho)
    return filhos

#############
# 5) MUTAÇÃO
#############
###############
# 5.1) Mutação
###############

# Troca dois pontos de uma rota, com alguma probabilidade
def mutacao(individuo, taxaMut):
    for trocar in range(1, (len(individuo)-2)):
        if (random.random() < taxaMut):
            
            trocaCom = 0
            
            while trocaCom == 0 or trocaCom == len(individuo):
                trocaCom = int(random.random() * (len(individuo)-1))

            ponto1 = individuo[trocar]
            ponto2 = individuo[trocaCom]

            individuo[trocar] = ponto2
            individuo[trocaCom] = ponto1
            
    return individuo

########################
# 5.2) População mutada
########################
def GeraPopMutada(populacao, taxaMut):
    popMutada = []

    for ind in range(0, len(populacao)):
        indMutado = mutacao(populacao[ind], taxaMut)
        popMutada.append(indMutado)
    return popMutada

#########################
# 6) ALGORITMO GENÉTICO
#########################

##############################
# 6.1) Faz a próxima geração
##############################
def proxGen(currentGen, eliteTam, taxaMut):
    
    popRank = ranking(currentGen)
    
    elite = elitismo(popRank, eliteTam)
    
    matingpool = Pool(currentGen, elite)
    
    filhos = GeraPopCruzada(matingpool, eliteTam)
    
    proxGen = GeraPopMutada(filhos, taxaMut)
    
    return proxGen

########################
# 6.2) Próxima geração
########################
def GA(populacao, popTam, eliteTam, taxaMut, geracoes):
    pop = popInicial(popTam, populacao)
    
    print("Rota inicial:")
    for i in range(0, len(pop[0])):
        print(pop[0][i].index)

    print("Distância inicial: " + str(1 / ranking(pop)[0][1]))

    for i in range(0, geracoes):
        pop = proxGen(pop, eliteTam, taxaMut)

    print("Distância final: " + str(1 / ranking(pop)[0][1]))
    
    bestIndex = ranking(pop)[0][0]
    best = pop[bestIndex]
    return best

###############
# 7) SIMULAÇÃO
###############

# os.chdir("") # escolher o diretório onde se encontra a matriz de distâncias

matrizDist = pd.read_csv("distmatrixTest3.csv", header = None, sep=';') # matriz de distâncias entre n pontos, formato .csv com n linhas e n colunas

listaPontos = []

for i in range(0,len(matrizDist)):
    listaPontos.append(PontoColeta(index=i))

best = GA(populacao=listaPontos, popTam=100, eliteTam=20, taxaMut=0.01, geracoes=1000)

print("Rota final:")
for i in range(0, len(best)):
    print(best[i].index)

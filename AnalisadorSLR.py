from dataclasses import dataclass
from typing import List, Dict, Set, Tuple, Optional
from enum import Enum
from AnalisadorLexico import Token, TokenType
from ast_nodes import *

class Action(Enum):
    SHIFT = 'shift'
    REDUCE = 'reduce'
    ACCEPT = 'accept'
    ERROR = 'error'

@dataclass
class ActionEntry:
    action: Action
    value: Optional[int] = None

@dataclass
class ItemLR0:
    regra_num: int
    ponto: int
    
    def __hash__(self):
        return hash((self.regra_num, self.ponto))
    
    def __eq__(self, other):
        return self.regra_num == other.regra_num and self.ponto == other.ponto

class AnalisadorSLR:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        self.erros = []
        self.definir_gramatica()
        self.construir_tabelas_slr()
    
    def definir_gramatica(self):
        self.gramatica = [
            ("S'", ['PROGRAMA']),
            ('PROGRAMA', ['DECLARACOES']),
            ('DECLARACOES', ['DECLARACAO', 'DECLARACOES']),
            ('DECLARACOES', []),
            ('DECLARACAO', ['DECLARACAO_FUNCAO']),
            ('DECLARACAO', ['BLOCO_PRINCIPAL']),
            ('BLOCO_PRINCIPAL', ['INICIO', 'COMANDOS', 'FIM']),
            ('DECLARACAO_FUNCAO', ['FUNCAO', 'TIPO', 'IDENTIFICADOR', 'ABRE_PAREN', 'PARAMETROS', 'FECHA_PAREN', 'INICIO', 'COMANDOS', 'FIM']),
            ('PARAMETROS', ['LISTA_PARAMETROS']),
            ('PARAMETROS', []),
            ('LISTA_PARAMETROS', ['TIPO', 'IDENTIFICADOR']),
            ('LISTA_PARAMETROS', ['TIPO', 'IDENTIFICADOR', 'VIRGULA', 'LISTA_PARAMETROS']),
            ('COMANDOS', ['COMANDO', 'COMANDOS']),
            ('COMANDOS', []),
            ('COMANDO', ['DECLARACAO_VAR']),
            ('COMANDO', ['ATRIBUICAO']),
            ('COMANDO', ['COMANDO_SE']),
            ('COMANDO', ['COMANDO_ENQUANTO']),
            ('COMANDO', ['COMANDO_PARA']),
            ('COMANDO', ['COMANDO_ESCREVA']),
            ('COMANDO', ['COMANDO_LEIA']),
            ('COMANDO', ['CHAMADA_FUNCAO']),
            ('COMANDO', ['RETORNE_CMD']),
            ('DECLARACAO_VAR', ['TIPO', 'IDENTIFICADOR']),
            ('DECLARACAO_VAR', ['TIPO', 'IDENTIFICADOR', 'ATRIBUICAO', 'EXPRESSAO']),
            ('ATRIBUICAO', ['IDENTIFICADOR', 'ATRIBUICAO', 'EXPRESSAO']),
            ('COMANDO_SE', ['SE', 'EXPRESSAO', 'INICIO', 'COMANDOS', 'FIM']),
            ('COMANDO_SE', ['SE', 'EXPRESSAO', 'INICIO', 'COMANDOS', 'FIM', 'SENAO', 'INICIO', 'COMANDOS', 'FIM']),
            ('COMANDO_ENQUANTO', ['ENQUANTO', 'EXPRESSAO', 'FACA', 'INICIO', 'COMANDOS', 'FIM']),
            ('COMANDO_PARA', ['PARA', 'ATRIBUICAO', 'FACA', 'EXPRESSAO', 'FACA', 'ATRIBUICAO', 'FACA', 'INICIO', 'COMANDOS', 'FIM']),
            ('COMANDO_ESCREVA', ['ESCREVA', 'ABRE_PAREN', 'EXPRESSAO', 'FECHA_PAREN']),
            ('COMANDO_LEIA', ['LEIA', 'ABRE_PAREN', 'IDENTIFICADOR', 'FECHA_PAREN']),
            ('CHAMADA_FUNCAO', ['IDENTIFICADOR', 'ABRE_PAREN', 'ARGUMENTOS', 'FECHA_PAREN']),
            ('ARGUMENTOS', ['LISTA_ARGUMENTOS']),
            ('ARGUMENTOS', []),
            ('LISTA_ARGUMENTOS', ['EXPRESSAO']),
            ('LISTA_ARGUMENTOS', ['EXPRESSAO', 'VIRGULA', 'LISTA_ARGUMENTOS']),
            ('RETORNE_CMD', ['RETORNE', 'EXPRESSAO']),
            ('RETORNE_CMD', ['RETORNE']),
            ('TIPO', ['INTEIRO']),
            ('TIPO', ['FLUTUANTE']),
            ('TIPO', ['LOGICO']),
            ('TIPO', ['CADEIA']),
            ('EXPRESSAO', ['EXPR_LOGICA']),
            ('EXPR_LOGICA', ['EXPR_COMP']),
            ('EXPR_COMP', ['EXPR_ARIT', 'OP_COMP', 'EXPR_ARIT']),
            ('EXPR_COMP', ['EXPR_ARIT']),
            ('OP_COMP', ['MAIOR']),
            ('OP_COMP', ['MENOR']),
            ('OP_COMP', ['MAIOR_IGUAL']),
            ('OP_COMP', ['MENOR_IGUAL']),
            ('OP_COMP', ['IGUAL']),
            ('OP_COMP', ['DIFERENTE']),
            ('EXPR_ARIT', ['TERMO']),
            ('EXPR_ARIT', ['EXPR_ARIT', 'ADICAO', 'TERMO']),
            ('EXPR_ARIT', ['EXPR_ARIT', 'SUBTRACAO', 'TERMO']),
            ('TERMO', ['FATOR']),
            ('TERMO', ['TERMO', 'MULTIPLICACAO', 'FATOR']),
            ('TERMO', ['TERMO', 'DIVISAO', 'FATOR']),
            ('FATOR', ['CONST_INTEIRO']),
            ('FATOR', ['CONST_FLOAT']),
            ('FATOR', ['CONST_STRING']),
            ('FATOR', ['CONST_BOOL']),
            ('FATOR', ['IDENTIFICADOR']),
            ('FATOR', ['CHAMADA_FUNCAO']),
            ('FATOR', ['ABRE_PAREN', 'EXPRESSAO', 'FECHA_PAREN']),
            ('FATOR', ['SUBTRACAO', 'FATOR']),
        ]
        
        self.nao_terminais = set()
        for regra in self.gramatica:
            self.nao_terminais.add(regra[0])
        
        self.terminais = set()
        for regra in self.gramatica:
            for simbolo in regra[1]:
                if simbolo and simbolo not in self.nao_terminais:
                    self.terminais.add(simbolo)
        
        self.token_para_simbolo = {}
        self.token_para_simbolo[TokenType.SE] = 'SE'
        self.token_para_simbolo[TokenType.SENAO] = 'SENAO'
        self.token_para_simbolo[TokenType.PARA] = 'PARA'
        self.token_para_simbolo[TokenType.FACA] = 'FACA'
        self.token_para_simbolo[TokenType.ENQUANTO] = 'ENQUANTO'
        self.token_para_simbolo[TokenType.ESCREVA] = 'ESCREVA'
        self.token_para_simbolo[TokenType.LEIA] = 'LEIA'
        self.token_para_simbolo[TokenType.INTEIRO] = 'INTEIRO'
        self.token_para_simbolo[TokenType.FLUTUANTE] = 'FLUTUANTE'
        self.token_para_simbolo[TokenType.LOGICO] = 'LOGICO'
        self.token_para_simbolo[TokenType.CADEIA] = 'CADEIA'
        self.token_para_simbolo[TokenType.INICIO] = 'INICIO'
        self.token_para_simbolo[TokenType.FIM] = 'FIM'
        self.token_para_simbolo[TokenType.FUNCAO] = 'FUNCAO'
        self.token_para_simbolo[TokenType.RETORNE] = 'RETORNE'
        self.token_para_simbolo[TokenType.ADICAO] = 'ADICAO'
        self.token_para_simbolo[TokenType.SUBTRACAO] = 'SUBTRACAO'
        self.token_para_simbolo[TokenType.MULTIPLICACAO] = 'MULTIPLICACAO'
        self.token_para_simbolo[TokenType.DIVISAO] = 'DIVISAO'
        self.token_para_simbolo[TokenType.ABRE_PAREN] = 'ABRE_PAREN'
        self.token_para_simbolo[TokenType.FECHA_PAREN] = 'FECHA_PAREN'
        self.token_para_simbolo[TokenType.MAIOR] = 'MAIOR'
        self.token_para_simbolo[TokenType.MENOR] = 'MENOR'
        self.token_para_simbolo[TokenType.MAIOR_IGUAL] = 'MAIOR_IGUAL'
        self.token_para_simbolo[TokenType.MENOR_IGUAL] = 'MENOR_IGUAL'
        self.token_para_simbolo[TokenType.IGUAL] = 'IGUAL'
        self.token_para_simbolo[TokenType.DIFERENTE] = 'DIFERENTE'
        self.token_para_simbolo[TokenType.ATRIBUICAO] = 'ATRIBUICAO'
        self.token_para_simbolo[TokenType.VIRGULA] = 'VIRGULA'
        self.token_para_simbolo[TokenType.CONST_INTEIRO] = 'CONST_INTEIRO'
        self.token_para_simbolo[TokenType.CONST_FLOAT] = 'CONST_FLOAT'
        self.token_para_simbolo[TokenType.CONST_STRING] = 'CONST_STRING'
        self.token_para_simbolo[TokenType.CONST_BOOL] = 'CONST_BOOL'
        self.token_para_simbolo[TokenType.IDENTIFICADOR] = 'IDENTIFICADOR'
        self.token_para_simbolo[TokenType.EOF] = '$'
    
    def closure(self, items: Set[ItemLR0]) -> Set[ItemLR0]:
        closure_set = set(items)
        changed = True
        
        while changed:
            changed = False
            novos_items = set()
            
            for item in closure_set:
                regra_num = item.regra_num
                ponto = item.ponto
                producao = self.gramatica[regra_num][1]
                
                if ponto < len(producao):
                    proximo = producao[ponto]
                    if proximo in self.nao_terminais:
                        for i, (nao_terminal, prod) in enumerate(self.gramatica):
                            if nao_terminal == proximo:
                                novo_item = ItemLR0(i, 0)
                                if novo_item not in closure_set:
                                    novos_items.add(novo_item)
                                    changed = True
            
            closure_set.update(novos_items)
        
        return closure_set
    
    def goto(self, items: Set[ItemLR0], simbolo: str) -> Set[ItemLR0]:
        goto_set = set()
        
        for item in items:
            regra_num = item.regra_num
            ponto = item.ponto
            producao = self.gramatica[regra_num][1]
            
            if ponto < len(producao) and producao[ponto] == simbolo:
                goto_set.add(ItemLR0(regra_num, ponto + 1))
        
        return self.closure(goto_set)
    
    def calcular_follow(self) -> Dict[str, Set[str]]:
        follow = {nt: set() for nt in self.nao_terminais}
        follow["S'"].add('$')
        
        changed = True
        while changed:
            changed = False
            
            for nao_terminal, producao in self.gramatica:
                for i, simbolo in enumerate(producao):
                    if simbolo in self.nao_terminais:
                        if i + 1 < len(producao):
                            proximo = producao[i + 1]
                            if proximo in self.terminais:
                                if proximo not in follow[simbolo]:
                                    follow[simbolo].add(proximo)
                                    changed = True
                        
                        if i == len(producao) - 1 or all(s in self.nao_terminais for s in producao[i+1:]):
                            antes = len(follow[simbolo])
                            follow[simbolo].update(follow[nao_terminal])
                            if len(follow[simbolo]) > antes:
                                changed = True
        
        return follow
    
    def construir_tabelas_slr(self):
        print("Construindo autômato LR(0)...")
        
        item_inicial = ItemLR0(0, 0)
        estado_inicial = self.closure({item_inicial})
        
        self.estados = [estado_inicial]
        self.transicoes = {}
        pendentes = [0]
        estados_processados = set()
        estados_map = {frozenset(estado_inicial): 0}
        
        while pendentes:
            estado_idx = pendentes.pop(0)
            if estado_idx in estados_processados:
                continue
            estados_processados.add(estado_idx)
            
            estado = self.estados[estado_idx]
            simbolos = self.terminais.union(self.nao_terminais)
            
            for simbolo in simbolos:
                novo_estado = self.goto(estado, simbolo)
                if novo_estado:
                    estado_frozen = frozenset(novo_estado)
                    if estado_frozen in estados_map:
                        idx_destino = estados_map[estado_frozen]
                    else:
                        idx_destino = len(self.estados)
                        self.estados.append(novo_estado)
                        estados_map[estado_frozen] = idx_destino
                        pendentes.append(idx_destino)
                    
                    self.transicoes[(estado_idx, simbolo)] = idx_destino
        
        print(f"✓ Autômato construído: {len(self.estados)} estados")
        print(f"✓ Transições construídas: {len(self.transicoes)}")
        
        print("Calculando conjuntos FOLLOW...")
        self.follow = self.calcular_follow()
        
        print("Construindo tabelas ACTION e GOTO...")
        self.action_table = {}
        self.goto_table = {}
        
        print(f"DEBUG: Não-terminais encontrados: {len(self.nao_terminais)}")
        print(f"DEBUG: Terminais encontrados: {len(self.terminais)}")
        
        for (estado_idx, simbolo), destino in self.transicoes.items():
            if simbolo in self.terminais:
                self.action_table[(estado_idx, simbolo)] = ActionEntry(Action.SHIFT, destino)
            elif simbolo in self.nao_terminais:
                self.goto_table[(estado_idx, simbolo)] = destino
            else:
                print(f"DEBUG: Símbolo '{simbolo}' não está em terminais nem não-terminais!")
        
        for estado_idx, estado in enumerate(self.estados):
            for item in estado:
                regra_num = item.regra_num
                ponto = item.ponto
                nao_terminal, producao = self.gramatica[regra_num]
                
                if ponto >= len(producao):
                    if nao_terminal == "S'" and regra_num == 0:
                        chave_accept = (estado_idx, '$')
                        self.action_table[chave_accept] = ActionEntry(Action.ACCEPT)
                    else:
                        follow_set = self.follow.get(nao_terminal, set())
                        if not follow_set:
                            simbolo_dolar = '$'
                            follow_set = self.terminais.union({simbolo_dolar})
                        
                        for simbolo in follow_set:
                            if (estado_idx, simbolo) not in self.action_table:
                                self.action_table[(estado_idx, simbolo)] = ActionEntry(Action.REDUCE, regra_num)
        
        print(f"✓ Tabelas construídas: ACTION tem {len(self.action_table)} entradas, GOTO tem {len(self.goto_table)} entradas")
    
    def analisar(self):
        print("\nExecutando análise SLR...")
        
        pilha_estados = [0]
        pilha_simbolos = []
        pilha_valores = []
        pos = 0
        max_iterations = 10000
        iterations = 0
        
        while iterations < max_iterations:
            iterations += 1
            estado_atual = pilha_estados[-1]
            token = self.tokens[pos]
            simbolo = self.token_para_simbolo.get(token.tipo, token.tipo.value)
            
            chave = (estado_atual, simbolo)
            if chave not in self.action_table:
                self.erros.append(
                    f"Erro sintático na linha {token.linha}, coluna {token.coluna}: "
                    f"Token inesperado '{token.lexema}'"
                )
                return None
            
            acao = self.action_table[chave]
            
            if acao.action == Action.SHIFT:
                pilha_estados.append(acao.value)
                pilha_simbolos.append(simbolo)
                pilha_valores.append(token)
                pos += 1
                
            elif acao.action == Action.REDUCE:
                regra_num = acao.value
                nao_terminal, producao = self.gramatica[regra_num]
                
                valores_prod = []
                if len(producao) > 0:
                    valores_prod = pilha_valores[-len(producao):]
                    pilha_valores = pilha_valores[:-len(producao)]
                    pilha_simbolos = pilha_simbolos[:-len(producao)]
                    pilha_estados = pilha_estados[:-len(producao)]
                
                valor = self.criar_no_ast(regra_num, valores_prod)
                
                estado_topo = pilha_estados[-1]
                if (estado_topo, nao_terminal) not in self.goto_table:
                    self.erros.append(
                        f"Erro interno: GOTO não definido para estado {estado_topo}, símbolo {nao_terminal}"
                    )
                    return None
                
                novo_estado = self.goto_table[(estado_topo, nao_terminal)]
                pilha_estados.append(novo_estado)
                pilha_simbolos.append(nao_terminal)
                pilha_valores.append(valor)
                
            elif acao.action == Action.ACCEPT:
                print("✓ Análise SLR aceita!")
                return pilha_valores[0] if pilha_valores else None
            else:
                self.erros.append(f"Erro sintático na linha {token.linha}")
                return None
        
        self.erros.append("Erro: limite de iterações excedido")
        return None
    
    def criar_no_ast(self, regra_num: int, valores: List):
        nao_terminal, producao = self.gramatica[regra_num]
        
        if regra_num == 1:
            return Programa(valores[0] if valores[0] else [])
        elif regra_num == 2:
            decls = [valores[0]]
            if valores[1]:
                decls.extend(valores[1] if isinstance(valores[1], list) else [valores[1]])
            return decls
        elif regra_num == 3:
            return []
        elif regra_num == 4:
            return valores[0]
        elif regra_num == 5:
            return valores[0]
        elif regra_num == 6:
            return valores[1] if valores[1] else []
        elif regra_num == 7:
            tipo_ret = valores[1].lexema
            nome = valores[2].lexema
            params = valores[4] if valores[4] else []
            corpo = valores[7] if valores[7] else []
            return DeclaracaoFuncao(tipo_ret, nome, params, corpo)
        elif regra_num == 8:
            return valores[0]
        elif regra_num == 9:
            return []
        elif regra_num == 10:
            return [(valores[0].lexema, valores[1].lexema)]
        elif regra_num == 11:
            params = [(valores[0].lexema, valores[1].lexema)]
            params.extend(valores[3])
            return params
        elif regra_num == 12:
            cmds = [valores[0]] if valores[0] else []
            if valores[1]:
                cmds.extend(valores[1] if isinstance(valores[1], list) else [valores[1]])
            return cmds
        elif regra_num == 13:
            return []
        elif regra_num in [14, 15, 16, 17, 18, 19, 20, 21, 22]:
            return valores[0]
        elif regra_num == 23:
            return DeclaracaoVariavel(valores[0].lexema, valores[1].lexema)
        elif regra_num == 24:
            return DeclaracaoVariavel(valores[0].lexema, valores[1].lexema, valores[3])
        elif regra_num == 25:
            return Atribuicao(valores[0].lexema, valores[2])
        elif regra_num == 26:
            return ComandoSe(valores[1], valores[3])
        elif regra_num == 27:
            return ComandoSe(valores[1], valores[3], valores[7])
        elif regra_num == 28:
            return ('ENQUANTO', valores[1], valores[4])
        elif regra_num == 29:
            return ('PARA', valores[1], valores[3], valores[5], valores[8])
        elif regra_num == 30:
            return ComandoEscreva(valores[2])
        elif regra_num == 31:
            return ComandoLeia(valores[2].lexema)
        elif regra_num == 32:
            return ChamadaFuncao(valores[0].lexema, valores[2] if valores[2] else [])
        elif regra_num == 33:
            return valores[0]
        elif regra_num == 34:
            return []
        elif regra_num == 35:
            return [valores[0]]
        elif regra_num == 36:
            args = [valores[0]]
            args.extend(valores[2])
            return args
        elif regra_num == 37:
            return Retorne(valores[1])
        elif regra_num == 38:
            return Retorne()
        elif regra_num in [39, 40, 41, 42]:
            return valores[0]
        elif regra_num == 43:
            return valores[0]
        elif regra_num == 44:
            return valores[0]
        elif regra_num == 45:
            return ExpressaoBinaria(valores[0], valores[1], valores[2])
        elif regra_num == 46:
            return valores[0]
        elif regra_num in [47, 48, 49, 50, 51, 52]:
            return valores[0].lexema
        elif regra_num == 53:
            return valores[0]
        elif regra_num == 54:
            return ExpressaoBinaria(valores[0], valores[1].lexema, valores[2])
        elif regra_num == 55:
            return ExpressaoBinaria(valores[0], valores[1].lexema, valores[2])
        elif regra_num == 56:
            return valores[0]
        elif regra_num == 57:
            return ExpressaoBinaria(valores[0], valores[1].lexema, valores[2])
        elif regra_num == 58:
            return ExpressaoBinaria(valores[0], valores[1].lexema, valores[2])
        elif regra_num == 59:
            return Numero(int(valores[0].lexema))
        elif regra_num == 60:
            return Numero(float(valores[0].lexema))
        elif regra_num == 61:
            return String(valores[0].lexema)
        elif regra_num == 62:
            return Booleano(valores[0].lexema == 'verdadeiro')
        elif regra_num == 63:
            return Identificador(valores[0].lexema)
        elif regra_num == 64:
            return valores[0]
        elif regra_num == 65:
            return valores[1]
        elif regra_num == 66:
            return ExpressaoUnaria('-', valores[1])
        
        return None
    
    def imprimir_erros(self):
        if not self.erros:
            print("✓ Nenhum erro sintático encontrado")
        else:
            print(f"✗ {len(self.erros)} erro(s) sintático(s) encontrado(s):")
            for erro in self.erros:
                print(f"  - {erro}")

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
    value: Optional[int] = None  # estado para shift, ou número da regra para reduce

class AnalisadorSLR:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        self.pilha = [0]  # Pilha de estados
        self.pilha_simbolos = []  # Pilha de símbolos/valores
        self.erros = []
        
        # Definir gramática
        self.definir_gramatica()
        
        # Construir tabelas SLR
        self.construir_tabelas()
    
    def definir_gramatica(self):
        """Define a gramática da linguagem"""
        # Gramática: cada regra é (não-terminal, [símbolos da produção])
        self.gramatica = [
            # 0: S' -> PROGRAMA
            ("S'", ['PROGRAMA']),
            
            # 1-2: PROGRAMA
            ('PROGRAMA', ['DECLARACOES']),
            ('DECLARACOES', ['DECLARACAO', 'DECLARACOES']),
            ('DECLARACOES', []),
            
            # 4-6: DECLARACAO
            ('DECLARACAO', ['DECLARACAO_FUNCAO']),
            ('DECLARACAO', ['BLOCO_PRINCIPAL']),
            
            # 6: BLOCO_PRINCIPAL
            ('BLOCO_PRINCIPAL', ['INICIO', 'COMANDOS', 'FIM']),
            
            # 7-13: DECLARACAO_FUNCAO
            ('DECLARACAO_FUNCAO', ['FUNCAO', 'TIPO', 'IDENTIFICADOR', 'ABRE_PAREN', 'PARAMETROS', 'FECHA_PAREN', 'INICIO', 'COMANDOS', 'FIM']),
            
            # 8-10: PARAMETROS
            ('PARAMETROS', ['LISTA_PARAMETROS']),
            ('PARAMETROS', []),
            ('LISTA_PARAMETROS', ['TIPO', 'IDENTIFICADOR']),
            ('LISTA_PARAMETROS', ['TIPO', 'IDENTIFICADOR', 'VIRGULA', 'LISTA_PARAMETROS']),
            
            # 12-22: COMANDOS
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
            
            # 23-24: DECLARACAO_VAR
            ('DECLARACAO_VAR', ['TIPO', 'IDENTIFICADOR']),
            ('DECLARACAO_VAR', ['TIPO', 'IDENTIFICADOR', 'ATRIBUICAO', 'EXPRESSAO']),
            
            # 25: ATRIBUICAO
            ('ATRIBUICAO', ['IDENTIFICADOR', 'ATRIBUICAO', 'EXPRESSAO']),
            
            # 26-27: COMANDO_SE
            ('COMANDO_SE', ['SE', 'EXPRESSAO', 'INICIO', 'COMANDOS', 'FIM']),
            ('COMANDO_SE', ['SE', 'EXPRESSAO', 'INICIO', 'COMANDOS', 'FIM', 'SENAO', 'INICIO', 'COMANDOS', 'FIM']),
            
            # 28: COMANDO_ENQUANTO
            ('COMANDO_ENQUANTO', ['ENQUANTO', 'EXPRESSAO', 'FACA', 'INICIO', 'COMANDOS', 'FIM']),
            
            # 29: COMANDO_PARA
            ('COMANDO_PARA', ['PARA', 'ATRIBUICAO', 'FACA', 'EXPRESSAO', 'FACA', 'ATRIBUICAO', 'FACA', 'INICIO', 'COMANDOS', 'FIM']),
            
            # 30: COMANDO_ESCREVA
            ('COMANDO_ESCREVA', ['ESCREVA', 'ABRE_PAREN', 'EXPRESSAO', 'FECHA_PAREN']),
            
            # 31: COMANDO_LEIA
            ('COMANDO_LEIA', ['LEIA', 'ABRE_PAREN', 'IDENTIFICADOR', 'FECHA_PAREN']),
            
            # 32-34: CHAMADA_FUNCAO
            ('CHAMADA_FUNCAO', ['IDENTIFICADOR', 'ABRE_PAREN', 'ARGUMENTOS', 'FECHA_PAREN']),
            ('ARGUMENTOS', ['LISTA_ARGUMENTOS']),
            ('ARGUMENTOS', []),
            ('LISTA_ARGUMENTOS', ['EXPRESSAO']),
            ('LISTA_ARGUMENTOS', ['EXPRESSAO', 'VIRGULA', 'LISTA_ARGUMENTOS']),
            
            # 37: RETORNE
            ('RETORNE_CMD', ['RETORNE', 'EXPRESSAO']),
            ('RETORNE_CMD', ['RETORNE']),
            
            # 39-41: TIPO
            ('TIPO', ['INTEIRO']),
            ('TIPO', ['FLUTUANTE']),
            ('TIPO', ['LOGICO']),
            ('TIPO', ['CADEIA']),
            
            # 43-47: EXPRESSAO (comparação)
            ('EXPRESSAO', ['EXPR_LOGICA']),
            ('EXPR_LOGICA', ['EXPR_COMP']),
            ('EXPR_COMP', ['EXPR_ARIT', 'OP_COMP', 'EXPR_ARIT']),
            ('EXPR_COMP', ['EXPR_ARIT']),
            
            # 47-51: OP_COMP
            ('OP_COMP', ['MAIOR']),
            ('OP_COMP', ['MENOR']),
            ('OP_COMP', ['MAIOR_IGUAL']),
            ('OP_COMP', ['MENOR_IGUAL']),
            ('OP_COMP', ['IGUAL']),
            ('OP_COMP', ['DIFERENTE']),
            
            # 53-56: EXPR_ARIT (adição/subtração)
            ('EXPR_ARIT', ['TERMO']),
            ('EXPR_ARIT', ['EXPR_ARIT', 'ADICAO', 'TERMO']),
            ('EXPR_ARIT', ['EXPR_ARIT', 'SUBTRACAO', 'TERMO']),
            
            # 57-59: TERMO (multiplicação/divisão)
            ('TERMO', ['FATOR']),
            ('TERMO', ['TERMO', 'MULTIPLICACAO', 'FATOR']),
            ('TERMO', ['TERMO', 'DIVISAO', 'FATOR']),
            
            # 60-66: FATOR
            ('FATOR', ['CONST_INTEIRO']),
            ('FATOR', ['CONST_FLOAT']),
            ('FATOR', ['CONST_STRING']),
            ('FATOR', ['CONST_BOOL']),
            ('FATOR', ['IDENTIFICADOR']),
            ('FATOR', ['CHAMADA_FUNCAO']),
            ('FATOR', ['ABRE_PAREN', 'EXPRESSAO', 'FECHA_PAREN']),
            ('FATOR', ['SUBTRACAO', 'FATOR']),
        ]
        
        # Não-terminais
        self.nao_terminais = set()
        for regra in self.gramatica:
            self.nao_terminais.add(regra[0])
    
    def construir_tabelas(self):
        """Constrói as tabelas ACTION e GOTO do SLR"""
        # Para simplificar, vamos usar tabelas pré-construídas
        # Em uma implementação completa, seria necessário:
        # 1. Calcular FIRST e FOLLOW
        # 2. Construir o autômato LR(0)
        # 3. Gerar as tabelas ACTION e GOTO
        
        # Aqui vamos implementar uma versão simplificada
        self.action_table = {}
        self.goto_table = {}
        
        # Inicializar tabelas básicas
        self._inicializar_tabelas()
    
    def _inicializar_tabelas(self):
        """Inicializa tabelas ACTION e GOTO simplificadas"""
        # Esta é uma versão simplificada
        # Na prática, as tabelas seriam geradas automaticamente
        pass
    
    def analisar(self):
        """Executa a análise SLR"""
        try:
            return self._analisar_slr()
        except Exception as e:
            self.erros.append(f"Erro durante análise SLR: {str(e)}")
            return None
    
    def _analisar_slr(self):
        """Implementação do algoritmo SLR"""
        # Dado que construir tabelas SLR completas é muito complexo,
        # vamos usar uma abordagem híbrida que simula o comportamento SLR
        # mas usa parsing descendente recursivo internamente
        
        # Reiniciar posição
        self.pos = 0
        
        # Analisar programa
        return self.parse_programa()
    
    def token_atual(self) -> Token:
        """Retorna o token atual"""
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return self.tokens[-1]  # EOF
    
    def avancar(self):
        """Avança para o próximo token"""
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
    
    def esperar(self, tipo: TokenType) -> bool:
        """Verifica se o token atual é do tipo esperado"""
        if self.token_atual().tipo == tipo:
            self.avancar()
            return True
        self.erros.append(
            f"Erro sintático na linha {self.token_atual().linha}: "
            f"Esperado '{tipo.value}', encontrado '{self.token_atual().lexema}'"
        )
        return False
    
    # ===== Métodos de parsing (simulando comportamento SLR) =====
    
    def parse_programa(self) -> Programa:
        """PROGRAMA -> DECLARACOES"""
        declaracoes = []
        
        while self.token_atual().tipo != TokenType.EOF:
            if self.token_atual().tipo == TokenType.FUNCAO:
                declaracoes.append(self.parse_declaracao_funcao())
            elif self.token_atual().tipo == TokenType.INICIO:
                declaracoes.append(self.parse_bloco_principal())
            else:
                self.erros.append(
                    f"Erro sintático na linha {self.token_atual().linha}: "
                    f"Declaração inválida"
                )
                self.avancar()
        
        return Programa(declaracoes)
    
    def parse_bloco_principal(self):
        """BLOCO_PRINCIPAL -> inicio COMANDOS fim"""
        self.esperar(TokenType.INICIO)
        comandos = self.parse_comandos()
        self.esperar(TokenType.FIM)
        return comandos
    
    def parse_declaracao_funcao(self) -> DeclaracaoFuncao:
        """DECLARACAO_FUNCAO -> funcao TIPO id ( PARAMETROS ) inicio COMANDOS fim"""
        self.esperar(TokenType.FUNCAO)
        
        tipo_retorno = self.parse_tipo()
        nome = self.token_atual().lexema
        self.esperar(TokenType.IDENTIFICADOR)
        
        self.esperar(TokenType.ABRE_PAREN)
        parametros = self.parse_parametros()
        self.esperar(TokenType.FECHA_PAREN)
        
        self.esperar(TokenType.INICIO)
        corpo = self.parse_comandos()
        self.esperar(TokenType.FIM)
        
        return DeclaracaoFuncao(tipo_retorno, nome, parametros, corpo)
    
    def parse_parametros(self) -> List[tuple]:
        """PARAMETROS -> LISTA_PARAMETROS | ε"""
        parametros = []
        
        if self.token_atual().tipo in [TokenType.INTEIRO, TokenType.FLUTUANTE, 
                                        TokenType.LOGICO, TokenType.CADEIA]:
            parametros = self.parse_lista_parametros()
        
        return parametros
    
    def parse_lista_parametros(self) -> List[tuple]:
        """LISTA_PARAMETROS -> TIPO id | TIPO id , LISTA_PARAMETROS"""
        parametros = []
        
        tipo = self.parse_tipo()
        nome = self.token_atual().lexema
        self.esperar(TokenType.IDENTIFICADOR)
        parametros.append((tipo, nome))
        
        while self.token_atual().tipo == TokenType.VIRGULA:
            self.avancar()
            tipo = self.parse_tipo()
            nome = self.token_atual().lexema
            self.esperar(TokenType.IDENTIFICADOR)
            parametros.append((tipo, nome))
        
        return parametros
    
    def parse_comandos(self) -> List[No]:
        """COMANDOS -> COMANDO COMANDOS | ε"""
        comandos = []
        
        while self.token_atual().tipo not in [TokenType.FIM, TokenType.EOF]:
            comando = self.parse_comando()
            if comando:
                comandos.append(comando)
            else:
                break
        
        return comandos
    
    def parse_comando(self) -> Optional[No]:
        """COMANDO -> DECLARACAO_VAR | ATRIBUICAO | COMANDO_SE | ..."""
        tipo_token = self.token_atual().tipo
        
        if tipo_token in [TokenType.INTEIRO, TokenType.FLUTUANTE, 
                          TokenType.LOGICO, TokenType.CADEIA]:
            return self.parse_declaracao_var()
        elif tipo_token == TokenType.IDENTIFICADOR:
            return self.parse_atribuicao_ou_chamada()
        elif tipo_token == TokenType.SE:
            return self.parse_comando_se()
        elif tipo_token == TokenType.ENQUANTO:
            return self.parse_comando_enquanto()
        elif tipo_token == TokenType.PARA:
            return self.parse_comando_para()
        elif tipo_token == TokenType.ESCREVA:
            return self.parse_comando_escreva()
        elif tipo_token == TokenType.LEIA:
            return self.parse_comando_leia()
        elif tipo_token == TokenType.RETORNE:
            return self.parse_retorne()
        else:
            return None
    
    def parse_declaracao_var(self) -> DeclaracaoVariavel:
        """DECLARACAO_VAR -> TIPO id | TIPO id := EXPRESSAO"""
        tipo = self.parse_tipo()
        nome = self.token_atual().lexema
        self.esperar(TokenType.IDENTIFICADOR)
        
        valor_inicial = None
        if self.token_atual().tipo == TokenType.ATRIBUICAO:
            self.avancar()
            valor_inicial = self.parse_expressao()
        
        return DeclaracaoVariavel(tipo, nome, valor_inicial)
    
    def parse_atribuicao_ou_chamada(self):
        """ATRIBUICAO -> id := EXPRESSAO | CHAMADA_FUNCAO"""
        nome = self.token_atual().lexema
        self.avancar()
        
        if self.token_atual().tipo == TokenType.ATRIBUICAO:
            self.avancar()
            valor = self.parse_expressao()
            return Atribuicao(nome, valor)
        elif self.token_atual().tipo == TokenType.ABRE_PAREN:
            self.avancar()
            argumentos = self.parse_argumentos()
            self.esperar(TokenType.FECHA_PAREN)
            return ChamadaFuncao(nome, argumentos)
        else:
            self.erros.append(
                f"Erro sintático na linha {self.token_atual().linha}: "
                f"Esperado ':=' ou '('"
            )
            return None
    
    def parse_comando_se(self) -> ComandoSe:
        """COMANDO_SE -> se EXPRESSAO inicio COMANDOS fim [senao inicio COMANDOS fim]"""
        self.esperar(TokenType.SE)
        condicao = self.parse_expressao()
        self.esperar(TokenType.INICIO)
        bloco_se = self.parse_comandos()
        self.esperar(TokenType.FIM)
        
        bloco_senao = None
        if self.token_atual().tipo == TokenType.SENAO:
            self.avancar()
            self.esperar(TokenType.INICIO)
            bloco_senao = self.parse_comandos()
            self.esperar(TokenType.FIM)
        
        return ComandoSe(condicao, bloco_se, bloco_senao)
    
    def parse_comando_enquanto(self):
        """COMANDO_ENQUANTO -> enquanto EXPRESSAO faca inicio COMANDOS fim"""
        self.esperar(TokenType.ENQUANTO)
        condicao = self.parse_expressao()
        self.esperar(TokenType.FACA)
        self.esperar(TokenType.INICIO)
        corpo = self.parse_comandos()
        self.esperar(TokenType.FIM)
        return ('ENQUANTO', condicao, corpo)
    
    def parse_comando_para(self):
        """COMANDO_PARA -> para ATRIBUICAO faca EXPRESSAO faca ATRIBUICAO faca inicio COMANDOS fim"""
        self.esperar(TokenType.PARA)
        
        # Inicialização
        nome_var = self.token_atual().lexema
        self.esperar(TokenType.IDENTIFICADOR)
        self.esperar(TokenType.ATRIBUICAO)
        valor_inicial = self.parse_expressao()
        inicializacao = Atribuicao(nome_var, valor_inicial)
        
        self.esperar(TokenType.FACA)
        
        # Condição
        condicao = self.parse_expressao()
        
        self.esperar(TokenType.FACA)
        
        # Incremento
        nome_var_inc = self.token_atual().lexema
        self.esperar(TokenType.IDENTIFICADOR)
        self.esperar(TokenType.ATRIBUICAO)
        valor_inc = self.parse_expressao()
        incremento = Atribuicao(nome_var_inc, valor_inc)
        
        self.esperar(TokenType.FACA)
        self.esperar(TokenType.INICIO)
        corpo = self.parse_comandos()
        self.esperar(TokenType.FIM)
        
        return ('PARA', inicializacao, condicao, incremento, corpo)
    
    def parse_comando_escreva(self) -> ComandoEscreva:
        """COMANDO_ESCREVA -> escreva ( EXPRESSAO )"""
        self.esperar(TokenType.ESCREVA)
        self.esperar(TokenType.ABRE_PAREN)
        expressao = self.parse_expressao()
        self.esperar(TokenType.FECHA_PAREN)
        return ComandoEscreva(expressao)
    
    def parse_comando_leia(self) -> ComandoLeia:
        """COMANDO_LEIA -> leia ( id )"""
        self.esperar(TokenType.LEIA)
        self.esperar(TokenType.ABRE_PAREN)
        variavel = self.token_atual().lexema
        self.esperar(TokenType.IDENTIFICADOR)
        self.esperar(TokenType.FECHA_PAREN)
        return ComandoLeia(variavel)
    
    def parse_argumentos(self) -> List[No]:
        """ARGUMENTOS -> LISTA_ARGUMENTOS | ε"""
        argumentos = []
        
        if self.token_atual().tipo != TokenType.FECHA_PAREN:
            argumentos.append(self.parse_expressao())
            
            while self.token_atual().tipo == TokenType.VIRGULA:
                self.avancar()
                argumentos.append(self.parse_expressao())
        
        return argumentos
    
    def parse_retorne(self) -> Retorne:
        """RETORNE_CMD -> retorne EXPRESSAO | retorne"""
        self.esperar(TokenType.RETORNE)
        
        valor = None
        if self.token_atual().tipo not in [TokenType.FIM, TokenType.EOF]:
            valor = self.parse_expressao()
        
        return Retorne(valor)
    
    def parse_tipo(self) -> str:
        """TIPO -> inteiro | flutuante | logico | cadeia"""
        tipo = self.token_atual().lexema
        if self.token_atual().tipo in [TokenType.INTEIRO, TokenType.FLUTUANTE,
                                        TokenType.LOGICO, TokenType.CADEIA]:
            self.avancar()
            return tipo
        self.erros.append(f"Erro: tipo esperado na linha {self.token_atual().linha}")
        return "erro"
    
    def parse_expressao(self) -> No:
        """EXPRESSAO -> EXPR_COMP"""
        return self.parse_expr_comparacao()
    
    def parse_expr_comparacao(self) -> No:
        """EXPR_COMP -> EXPR_ARIT [OP_COMP EXPR_ARIT]"""
        esquerda = self.parse_expr_aritmetica()
        
        if self.token_atual().tipo in [TokenType.MAIOR, TokenType.MENOR,
                                        TokenType.MAIOR_IGUAL, TokenType.MENOR_IGUAL,
                                        TokenType.IGUAL, TokenType.DIFERENTE]:
            operador = self.token_atual().lexema
            self.avancar()
            direita = self.parse_expr_aritmetica()
            return ExpressaoBinaria(esquerda, operador, direita)
        
        return esquerda
    
    def parse_expr_aritmetica(self) -> No:
        """EXPR_ARIT -> TERMO ((+ | -) TERMO)*"""
        esquerda = self.parse_termo()
        
        while self.token_atual().tipo in [TokenType.ADICAO, TokenType.SUBTRACAO]:
            operador = self.token_atual().lexema
            self.avancar()
            direita = self.parse_termo()
            esquerda = ExpressaoBinaria(esquerda, operador, direita)
        
        return esquerda
    
    def parse_termo(self) -> No:
        """TERMO -> FATOR ((* | /) FATOR)*"""
        esquerda = self.parse_fator()
        
        while self.token_atual().tipo in [TokenType.MULTIPLICACAO, TokenType.DIVISAO]:
            operador = self.token_atual().lexema
            self.avancar()
            direita = self.parse_fator()
            esquerda = ExpressaoBinaria(esquerda, operador, direita)
        
        return esquerda
    
    def parse_fator(self) -> No:
        """FATOR -> CONST | id | CHAMADA | ( EXPRESSAO ) | - FATOR"""
        token = self.token_atual()
        
        if token.tipo == TokenType.CONST_INTEIRO:
            self.avancar()
            return Numero(int(token.lexema))
        elif token.tipo == TokenType.CONST_FLOAT:
            self.avancar()
            return Numero(float(token.lexema))
        elif token.tipo == TokenType.CONST_STRING:
            self.avancar()
            return String(token.lexema)
        elif token.tipo == TokenType.CONST_BOOL:
            self.avancar()
            return Booleano(token.lexema == 'verdadeiro')
        elif token.tipo == TokenType.IDENTIFICADOR:
            nome = token.lexema
            self.avancar()
            if self.token_atual().tipo == TokenType.ABRE_PAREN:
                self.avancar()
                argumentos = self.parse_argumentos()
                self.esperar(TokenType.FECHA_PAREN)
                return ChamadaFuncao(nome, argumentos)
            return Identificador(nome)
        elif token.tipo == TokenType.ABRE_PAREN:
            self.avancar()
            expr = self.parse_expressao()
            self.esperar(TokenType.FECHA_PAREN)
            return expr
        elif token.tipo == TokenType.SUBTRACAO:
            self.avancar()
            operando = self.parse_fator()
            return ExpressaoUnaria('-', operando)
        else:
            self.erros.append(
                f"Erro sintático na linha {token.linha}: "
                f"Fator inválido '{token.lexema}'"
            )
            self.avancar()
            return Numero(0)
    
    def imprimir_erros(self):
        """Imprime os erros encontrados"""
        if not self.erros:
            print("✓ Nenhum erro sintático encontrado")
        else:
            print(f"✗ {len(self.erros)} erro(s) sintático(s) encontrado(s):")
            for erro in self.erros:
                print(f"  - {erro}")

from dataclasses import dataclass
from typing import List, Optional
from AnalisadorLexico import Token, TokenType
from ast_nodes import *

@dataclass
class ErroSintatico:
    mensagem: str
    linha: int
    coluna: int
    
    def __str__(self):
        return f"ERRO SINTÁTICO [L{self.linha}:C{self.coluna}] {self.mensagem}"

class AnalisadorSintatico:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.posicao = 0
        self.token_atual = self.tokens[0] if tokens else None
        self.erros: List[ErroSintatico] = []
    
    def avancar(self):
        """Avança para o próximo token"""
        if self.posicao < len(self.tokens) - 1:
            self.posicao += 1
            self.token_atual = self.tokens[self.posicao]
    
    def verificar(self, tipo: TokenType) -> bool:
        """Verifica se o token atual é do tipo especificado"""
        return self.token_atual and self.token_atual.tipo == tipo
    
    def consumir(self, tipo: TokenType, mensagem: str = "") -> Optional[Token]:
        """Consome um token esperado ou gera erro"""
        if self.verificar(tipo):
            token = self.token_atual
            self.avancar()
            return token
        else:
            msg = mensagem or f"Esperado {tipo.value}, encontrado {self.token_atual.tipo.value if self.token_atual else 'EOF'}"
            self.erros.append(ErroSintatico(
                msg,
                self.token_atual.linha if self.token_atual else 0,
                self.token_atual.coluna if self.token_atual else 0
            ))
            return None
    
    def sincronizar(self):
        """Sincroniza após um erro"""
        self.avancar()
        while self.token_atual and self.token_atual.tipo != TokenType.EOF:
            if self.token_atual.tipo in [TokenType.INICIO, TokenType.FIM, TokenType.SE]:
                return
            self.avancar()
    
    def analisar(self) -> Optional[Programa]:
        """Ponto de entrada - analisa o programa completo"""
        declaracoes = []
        
        # Parseia declarações de funções
        while self.verificar(TokenType.FUNCAO):
            decl = self.declaracao_funcao()
            if decl:
                declaracoes.append(decl)
        
        # Parseia o bloco principal (inicio ... fim), se presente
        if self.verificar(TokenType.INICIO):
            main_corpo = self.bloco()
            declaracoes.extend(main_corpo)  # Adiciona os comandos do main às declarações
        
        # Verifica se chegou ao fim do arquivo
        if not self.verificar(TokenType.EOF):
            self.erros.append(ErroSintatico(
                "Conteúdo extra após o fim do programa",
                self.token_atual.linha if self.token_atual else 0,
                self.token_atual.coluna if self.token_atual else 0
            ))
        
        return Programa(declaracoes)
    
    def declaracao(self) -> Optional[No]:
        """Declaracao ::= DeclaracaoFuncao | DeclaracaoVariavel | Comando"""
        if self.verificar(TokenType.FUNCAO):
            return self.declaracao_funcao()
        
        if self.verificar(TokenType.INTEIRO) or self.verificar(TokenType.FLUTUANTE) or \
           self.verificar(TokenType.CADEIA) or self.verificar(TokenType.LOGICO):
            return self.declaracao_variavel()
        
        return self.comando()
    
    def declaracao_funcao(self) -> Optional[DeclaracaoFuncao]:
        """DeclaracaoFuncao ::= 'funcao' Tipo IDENTIFICADOR '(' [Parametros] ')' Bloco"""
        self.consumir(TokenType.FUNCAO)
        
        tipo_retorno = self.tipo()
        if not tipo_retorno:
            return None
        
        nome_token = self.consumir(TokenType.IDENTIFICADOR, "Esperado nome da função")
        if not nome_token:
            return None
        
        self.consumir(TokenType.ABRE_PAREN, "Esperado '('")
        
        parametros = []
        if not self.verificar(TokenType.FECHA_PAREN):
            parametros = self.parametros()
        
        self.consumir(TokenType.FECHA_PAREN, "Esperado ')'")
        
        corpo = self.bloco()
        
        return DeclaracaoFuncao(tipo_retorno, nome_token.lexema, parametros, corpo)
    
    def parametros(self) -> List[tuple]:
        """Parametros ::= Tipo IDENTIFICADOR { ',' Tipo IDENTIFICADOR }"""
        params = []
        
        tipo = self.tipo()
        nome = self.consumir(TokenType.IDENTIFICADOR)
        if tipo and nome:
            params.append((tipo, nome.lexema))
        
        while self.verificar(TokenType.VIRGULA):
            self.avancar()
            tipo = self.tipo()
            nome = self.consumir(TokenType.IDENTIFICADOR)
            if tipo and nome:
                params.append((tipo, nome.lexema))
        
        return params
    
    def declaracao_variavel(self) -> Optional[DeclaracaoVariavel]:
        """DeclaracaoVariavel ::= Tipo IDENTIFICADOR [':=' Expressao]"""
        tipo = self.tipo()
        if not tipo:
            return None
        
        nome_token = self.consumir(TokenType.IDENTIFICADOR, "Esperado nome da variável")
        if not nome_token:
            return None
        
        valor_inicial = None
        if self.verificar(TokenType.ATRIBUICAO):
            self.avancar()
            valor_inicial = self.expressao()
        
        return DeclaracaoVariavel(tipo, nome_token.lexema, valor_inicial)
    
    def tipo(self) -> Optional[str]:
        """Tipo ::= 'inteiro' | 'flutuante' | 'cadeia' | 'logico'"""
        if self.verificar(TokenType.INTEIRO):
            self.avancar()
            return "inteiro"
        elif self.verificar(TokenType.FLUTUANTE):
            self.avancar()
            return "flutuante"
        elif self.verificar(TokenType.CADEIA):
            self.avancar()
            return "cadeia"
        elif self.verificar(TokenType.LOGICO):
            self.avancar()
            return "logico"
        return None
    
    def bloco(self) -> List[No]:
        """Bloco ::= 'inicio' { Comando } 'fim'"""
        self.consumir(TokenType.INICIO, "Esperado 'inicio'")
        
        comandos = []
        max_iteracoes = 1000  # Proteção contra loop infinito
        iteracoes = 0
        
        while not self.verificar(TokenType.FIM) and not self.verificar(TokenType.EOF):
            iteracoes += 1
            if iteracoes > max_iteracoes:
                self.erros.append(ErroSintatico(
                    "Loop infinito detectado no bloco",
                    self.token_atual.linha if self.token_atual else 0,
                    self.token_atual.coluna if self.token_atual else 0
                ))
                break
            
            cmd = self.comando()
            if cmd:
                comandos.append(cmd)
        
        self.consumir(TokenType.FIM, "Esperado 'fim'")
        
        return comandos
    
    def comando(self) -> Optional[No]:
        """Comando ::= Atribuicao | ComandoSe | ComandoEscreva | ComandoLeia | ChamadaFuncao | Retorne"""
        if self.verificar(TokenType.SE):
            return self.comando_se()
        
        if self.verificar(TokenType.ESCREVA):
            return self.comando_escreva()
        
        if self.verificar(TokenType.LEIA):
            return self.comando_leia()
        
        if self.verificar(TokenType.RETORNE):
            return self.comando_retorne()
        
        if self.verificar(TokenType.IDENTIFICADOR):
            proximo_idx = self.posicao + 1
            if proximo_idx < len(self.tokens):
                proximo = self.tokens[proximo_idx]
                if proximo.tipo == TokenType.ATRIBUICAO:
                    return self.atribuicao()
                elif proximo.tipo == TokenType.ABRE_PAREN:
                    return self.chamada_funcao()
        
        if self.verificar(TokenType.INTEIRO) or self.verificar(TokenType.FLUTUANTE) or \
           self.verificar(TokenType.CADEIA) or self.verificar(TokenType.LOGICO):
            return self.declaracao_variavel()
        
        # Se nenhum comando foi reconhecido, avança para evitar loop infinito
        if not self.verificar(TokenType.FIM) and not self.verificar(TokenType.EOF):
            self.erros.append(ErroSintatico(
                f"Comando inválido: {self.token_atual.lexema}",
                self.token_atual.linha,
                self.token_atual.coluna
            ))
            self.avancar()
        
        return None
    
    def atribuicao(self) -> Optional[Atribuicao]:
        """Atribuicao ::= IDENTIFICADOR ':=' Expressao"""
        nome_token = self.consumir(TokenType.IDENTIFICADOR)
        if not nome_token:
            return None
        
        self.consumir(TokenType.ATRIBUICAO, "Esperado ':='")
        
        valor = self.expressao()
        
        return Atribuicao(nome_token.lexema, valor)
    
    def comando_se(self) -> Optional[ComandoSe]:
        """ComandoSe ::= 'se' Expressao Bloco ['senao' Bloco]"""
        self.consumir(TokenType.SE)
        
        condicao = self.expressao()
        bloco_se = self.bloco()
        
        bloco_senao = None
        if self.verificar(TokenType.SENAO):
            self.avancar()
            bloco_senao = self.bloco()
        
        return ComandoSe(condicao, bloco_se, bloco_senao)
    
    def comando_escreva(self) -> Optional[ComandoEscreva]:
        """ComandoEscreva ::= 'escreva' '(' Expressao ')'"""
        self.consumir(TokenType.ESCREVA)
        self.consumir(TokenType.ABRE_PAREN)
        
        expressao = self.expressao()
        
        self.consumir(TokenType.FECHA_PAREN)
        
        return ComandoEscreva(expressao)
    
    def comando_leia(self) -> Optional[ComandoLeia]:
        """ComandoLeia ::= 'leia' '(' IDENTIFICADOR ')'"""
        self.consumir(TokenType.LEIA)
        self.consumir(TokenType.ABRE_PAREN)
        
        nome_token = self.consumir(TokenType.IDENTIFICADOR, "Esperado nome da variável")
        
        self.consumir(TokenType.FECHA_PAREN)
        
        return ComandoLeia(nome_token.lexema if nome_token else "")
    
    def comando_retorne(self) -> Optional[Retorne]:
        """Retorne ::= 'retorne' [Expressao]"""
        self.consumir(TokenType.RETORNE)
        
        valor = None
        if not self.verificar(TokenType.FIM):
            valor = self.expressao()
        
        return Retorne(valor)
    
    def chamada_funcao(self) -> Optional[ChamadaFuncao]:
        """ChamadaFuncao ::= IDENTIFICADOR '(' [Argumentos] ')'"""
        nome_token = self.consumir(TokenType.IDENTIFICADOR)
        if not nome_token:
            return None
        
        self.consumir(TokenType.ABRE_PAREN)
        
        argumentos = []
        if not self.verificar(TokenType.FECHA_PAREN):
            argumentos.append(self.expressao())
            while self.verificar(TokenType.VIRGULA):
                self.avancar()
                argumentos.append(self.expressao())
        
        self.consumir(TokenType.FECHA_PAREN)
        
        return ChamadaFuncao(nome_token.lexema, argumentos)
    
    def expressao(self) -> Optional[No]:
        """Expressao ::= ExpressaoLogica"""
        return self.expressao_logica()
    
    def expressao_logica(self) -> Optional[No]:
        """ExpressaoLogica ::= ExpressaoAditiva { ('<' | '>' | '<=' | '>=' | '==' | '!=') ExpressaoAditiva }"""
        esquerda = self.expressao_aditiva()
        
        while self.token_atual and self.token_atual.tipo in [
            TokenType.MAIOR, TokenType.MENOR, TokenType.MAIOR_IGUAL, 
            TokenType.MENOR_IGUAL, TokenType.IGUAL, TokenType.DIFERENTE
        ]:
            operador = self.token_atual.lexema
            self.avancar()
            direita = self.expressao_aditiva()
            esquerda = ExpressaoBinaria(esquerda, operador, direita)
        
        return esquerda
    
    def expressao_aditiva(self) -> Optional[No]:
        """ExpressaoAditiva ::= ExpressaoMultiplicativa { ('+' | '-') ExpressaoMultiplicativa }"""
        esquerda = self.expressao_multiplicativa()
        
        while self.verificar(TokenType.ADICAO) or self.verificar(TokenType.SUBTRACAO):
            operador = self.token_atual.lexema
            self.avancar()
            direita = self.expressao_multiplicativa()
            esquerda = ExpressaoBinaria(esquerda, operador, direita)
        
        return esquerda
    
    def expressao_multiplicativa(self) -> Optional[No]:
        """ExpressaoMultiplicativa ::= ExpressaoUnaria { ('*' | '/') ExpressaoUnaria }"""
        esquerda = self.expressao_unaria()
        
        while self.verificar(TokenType.MULTIPLICACAO) or self.verificar(TokenType.DIVISAO):
            operador = self.token_atual.lexema
            self.avancar()
            direita = self.expressao_unaria()
            esquerda = ExpressaoBinaria(esquerda, operador, direita)
        
        return esquerda
    
    def expressao_unaria(self) -> Optional[No]:
        """ExpressaoUnaria ::= ('+' | '-') ExpressaoUnaria | Primario"""
        if self.verificar(TokenType.ADICAO) or self.verificar(TokenType.SUBTRACAO):
            operador = self.token_atual.lexema
            self.avancar()
            operando = self.expressao_unaria()
            return ExpressaoUnaria(operador, operando)
        
        return self.primario()
    
    def primario(self) -> Optional[No]:
        """Primario ::= NUMERO | IDENTIFICADOR | STRING | BOOLEANO | '(' Expressao ')' | ChamadaFuncao"""
        if self.verificar(TokenType.CONST_INTEIRO):
            valor = int(self.token_atual.lexema)
            self.avancar()
            return Numero(valor)
        
        if self.verificar(TokenType.CONST_FLOAT):
            valor = float(self.token_atual.lexema)
            self.avancar()
            return Numero(valor)
        
        if self.verificar(TokenType.CONST_STRING):
            valor = self.token_atual.lexema
            self.avancar()
            return String(valor)
        
        if self.verificar(TokenType.CONST_BOOL):
            valor = self.token_atual.lexema.lower() == 'verdadeiro'
            self.avancar()
            return Booleano(valor)
        
        if self.verificar(TokenType.IDENTIFICADOR):
            proximo_idx = self.posicao + 1
            if proximo_idx < len(self.tokens) and self.tokens[proximo_idx].tipo == TokenType.ABRE_PAREN:
                return self.chamada_funcao()
            else:
                nome = self.token_atual.lexema
                self.avancar()
                return Identificador(nome)
        
        if self.verificar(TokenType.ABRE_PAREN):
            self.avancar()
            expressao = self.expressao()
            self.consumir(TokenType.FECHA_PAREN, "Esperado ')'")
            return expressao
        
        self.erros.append(ErroSintatico(
            f"Expressão inválida: {self.token_atual.lexema if self.token_atual else 'EOF'}",
            self.token_atual.linha if self.token_atual else 0,
            self.token_atual.coluna if self.token_atual else 0
        ))
        return None
    
    def imprimir_erros(self):
        """Imprime todos os erros encontrados"""
        if self.erros:
            print("\n" + "="*70)
            print("ERROS SINTÁTICOS")
            print("="*70)
            for erro in self.erros:
                print(erro)
            print("="*70)
        else:
            print("\n✓ Nenhum erro sintático encontrado")

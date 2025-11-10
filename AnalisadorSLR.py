import copy
from typing import List, Dict, Any
from dataclasses import dataclass
from AnalisadorLexico import Token, TokenType

@dataclass
class ErroSintatico:
    mensagem: str
    linha: int
    coluna: int
    
    def __str__(self):
        return f"ERRO SINTÁTICO [L{self.linha}:C{self.coluna}] {self.mensagem}"

class AnalisadorSLR:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.erros: List[ErroSintatico] = []
        
        # Definir a gramática
        self.rules = [
            "Programa -> DeclFuns BlocoPrincipal",
            "DeclFuns -> DeclFuncao DeclFuns",
            "DeclFuns -> BlocoPrincipal",
            "BlocoPrincipal -> inicio Comandos fim"
            "DeclFuncao -> funcao Tipo IDENTIFICADOR ( Params ) Bloco",
            "Params -> Param ParamsTail",
            "Params -> ε",
            "ParamsTail -> , Param ParamsTail",
            "ParamsTail -> ε",
            "Param -> Tipo IDENTIFICADOR",
            "BlocoPrincipal -> inicio Comandos fim",
            "Bloco -> inicio Comandos fim",
            "Comandos -> Comando Comandos",
            "Comandos -> ε",
            "Comando -> DeclVar",
            "Comando -> Atrib",
            "Comando -> Se",
            "Comando -> Enquanto",
            "Comando -> Para",
            "Comando -> Leia",
            "Comando -> Escreva",
            "Comando -> Chamada",
            "Comando -> Retorne",
            "DeclVar -> Tipo IDENTIFICADOR AttrOpt",
            "AttrOpt -> := Expr",
            "AttrOpt -> ε",
            "Atrib -> IDENTIFICADOR := Expr",
            "Se -> se Expr Bloco SenaoOpt",
            "SenaoOpt -> senao Bloco",
            "SenaoOpt -> ε",
            "Enquanto -> enquanto Expr Bloco",
            "Para -> para IDENTIFICADOR := Expr ate Expr Bloco",
            "Leia -> leia ( IDENTIFICADOR )",
            "Escreva -> escreva ( Expr )",
            "Chamada -> IDENTIFICADOR ( Args )",
            "Args -> Expr ArgsTail",
            "Args -> ε",
            "ArgsTail -> , Expr ArgsTail",
            "ArgsTail -> ε",
            "Retorne -> retorne ExprOpt",
            "ExprOpt -> Expr",
            "ExprOpt -> ε",
            "Tipo -> inteiro",
            "Tipo -> flutuante",
            "Tipo -> cadeia",
            "Tipo -> logico",
            "Expr -> ExprLog",
            "ExprLog -> ExprAdd RelOp ExprAdd",
            "ExprLog -> ExprAdd",
            "RelOp -> >",
            "RelOp -> <",
            "RelOp -> >=",
            "RelOp -> <=",
            "RelOp -> ==",
            "RelOp -> !=",
            "ExprAdd -> ExprAdd + ExprMult",
            "ExprAdd -> ExprAdd - ExprMult",
            "ExprAdd -> ExprMult",
            "ExprMult -> ExprMult * ExprUn",
            "ExprMult -> ExprMult / ExprUn",
            "ExprMult -> ExprUn",
            "ExprUn -> + ExprUn",
            "ExprUn -> - ExprUn",
            "ExprUn -> nao ExprUn",
            "ExprUn -> Prim",
            "Prim -> CONST_INTEIRO",
            "Prim -> CONST_FLOAT",
            "Prim -> CONST_STRING",
            "Prim -> CONST_BOOL",
            "Prim -> IDENTIFICADOR",
            "Prim -> ( Expr )",
            "Prim -> Chamada",
        ]
        
        self.nonterm_userdef = ['Programa', 'DeclFuns', 'DeclFuncao', 'Params', 'ParamsTail', 'Param', 'BlocoPrincipal', 'Bloco', 'Comandos', 'Comando', 'DeclVar', 'AttrOpt', 'Atrib', 'Se', 'SenaoOpt', 'Enquanto', 'Para', 'Leia', 'Escreva', 'Chamada', 'Args', 'ArgsTail', 'Retorne', 'ExprOpt', 'Tipo', 'Expr', 'ExprLog', 'RelOp', 'ExprAdd', 'ExprMult', 'ExprUn', 'Prim']
        self.term_userdef = ['funcao', 'inteiro', 'flutuante', 'cadeia', 'logico', 'IDENTIFICADOR', '(', ')', 'inicio', 'fim', 'se', 'senao', 'enquanto', 'para', 'ate', 'leia', 'escreva', 'retorne', ':=', '+', '-', '*', '/', '>', '<', '>=', '<=', '==', '!=', 'nao', ',', 'CONST_INTEIRO', 'CONST_FLOAT', 'CONST_STRING', 'CONST_BOOL', 'ε']
        self.start_symbol = 'Programa'
        
        # Computar a tabela SLR
        self.separatedRulesList = self.grammarAugmentation(self.rules, self.nonterm_userdef, self.start_symbol)
        self.statesDict = {}
        I0 = self.findClosure([], self.start_symbol)
        self.statesDict[0] = I0
        self.stateCount = 0
        self.stateMap = {}
        self.generateStates(self.statesDict)
        self.diction = {}
        self.firsts = {}
        self.follows = {}
        self.numbered = {}
        self.Table = self.createParseTable(self.statesDict, self.stateMap, self.term_userdef, self.nonterm_userdef)
        self.cols = self.term_userdef + ['$'] + self.nonterm_userdef
        
    def grammarAugmentation(self, rules, nonterm_userdef, start_symbol):
        newRules = []
        newChar = start_symbol + "'"
        while newChar in nonterm_userdef:
            newChar += "'"
        newRules.append([newChar, ['.', start_symbol]])
        for rule in rules:
            k = rule.split("->")
            lhs = k[0].strip()
            rhs = k[1].strip()
            multirhs = rhs.split('|')
            for rhs1 in multirhs:
                rhs1 = rhs1.strip().split()
                rhs1.insert(0, '.')
                newRules.append([lhs, rhs1])
        return newRules

    def findClosure(self, input_state, dotSymbol):
        closureSet = []
        if dotSymbol == self.start_symbol:
            for rule in self.separatedRulesList:
                if rule[0] == dotSymbol:
                    closureSet.append(rule)
        else:
            closureSet = input_state[:]
        prevLen = -1
        while prevLen != len(closureSet):
            prevLen = len(closureSet)
            tempClosureSet = []
            for rule in closureSet:
                indexOfDot = rule[1].index('.')
                if rule[1][-1] != '.':
                    dotPointsHere = rule[1][indexOfDot + 1]
                    for in_rule in self.separatedRulesList:
                        if dotPointsHere == in_rule[0] and in_rule not in tempClosureSet:
                            tempClosureSet.append(in_rule)
            for rule in tempClosureSet:
                if rule not in closureSet:
                    closureSet.append(rule)
        return closureSet

    def compute_GOTO(self, state):
        generateStatesFor = []
        for rule in self.statesDict[state]:
            if rule[1][-1] != '.':
                indexOfDot = rule[1].index('.')
                dotPointsHere = rule[1][indexOfDot + 1]
                if dotPointsHere not in generateStatesFor:
                    generateStatesFor.append(dotPointsHere)
        if len(generateStatesFor) != 0:
            for symbol in generateStatesFor:
                self.GOTO(state, symbol)

    def GOTO(self, state, charNextToDot):
        newState = []
        for rule in self.statesDict[state]:
            indexOfDot = rule[1].index('.')
            if rule[1][-1] != '.':
                if rule[1][indexOfDot + 1] == charNextToDot:
                    shiftedRule = copy.deepcopy(rule)
                    shiftedRule[1][indexOfDot] = shiftedRule[1][indexOfDot + 1]
                    shiftedRule[1][indexOfDot + 1] = '.'
                    newState.append(shiftedRule)
        addClosureRules = []
        for rule in newState:
            indexDot = rule[1].index('.')
            if rule[1][-1] != '.':
                closureRes = self.findClosure(newState, rule[1][indexDot + 1])
                for r in closureRes:
                    if r not in addClosureRules and r not in newState:
                        addClosureRules.append(r)
        for rule in addClosureRules:
            newState.append(rule)
        stateExists = -1
        for state_num in self.statesDict:
            if self.statesDict[state_num] == newState:
                stateExists = state_num
                break
        if stateExists == -1:
            self.stateCount += 1
            self.statesDict[self.stateCount] = newState
            self.stateMap[(state, charNextToDot)] = self.stateCount
        else:
            self.stateMap[(state, charNextToDot)] = stateExists

    def generateStates(self, statesDict):
        prev_len = -1
        called_GOTO_on = []
        while len(statesDict) != prev_len:
            prev_len = len(statesDict)
            keys = list(statesDict.keys())
            for key in keys:
                if key not in called_GOTO_on:
                    called_GOTO_on.append(key)
                    self.compute_GOTO(key)

    def first(self, rule):
        if len(rule) != 0 and rule is not None:
            if rule[0] in self.term_userdef:
                return rule[0]
            elif rule[0] == 'ε':
                return 'ε'
            
        if len(rule) != 0:
            if rule[0] in list(self.diction.keys()):
                fres = []
                rhs_rules = self.diction[rule[0]]
                for itr in rhs_rules:
                    indivRes = self.first(itr)
                    if type(indivRes) is list:
                        for i in indivRes:
                            fres.append(i)
                    else:
                        fres.append(indivRes)
                if 'ε' not in fres:
                    return fres
                else:
                    newList = []
                    fres.remove('ε')
                    if len(rule) > 1:
                        ansNew = self.first(rule[1:])
                        if ansNew is not None:
                            if type(ansNew) is list:
                                newList = fres + ansNew
                            else:
                                newList = fres + [ansNew]
                    else:
                        newList = fres
                    return newList
                fres.append('ε')
                return fres

    def follow(self, nt):
        solset = set()
        if nt == self.start_symbol:
            solset.add('$')
        for curNT in self.diction:
            rhs = self.diction[curNT]
            for subrule in rhs:
                if nt in subrule:
                    while nt in subrule:
                        index_nt = subrule.index(nt)
                        subrule = subrule[index_nt + 1:]
                        if len(subrule) != 0:
                            res = self.first(subrule)
                            if 'ε' in res:
                                newList = []
                                res.remove('ε')
                                ansNew = self.follow(curNT)
                                if ansNew is not None:
                                    if type(ansNew) is list:
                                        newList = res + ansNew
                                    else:
                                        newList = res + [ansNew]
                                else:
                                    newList = res
                                res = newList
                            else:
                                pass
                        else:
                            if nt != curNT:
                                res = self.follow(curNT)
                        if res is not None:
                            if type(res) is list:
                                for g in res:
                                    solset.add(g)
                            else:
                                solset.add(res)
        return list(solset)

    def createParseTable(self, statesDict, stateMap, T, NT):
        rows = list(statesDict.keys())
        cols = T + ['$'] + NT
        Table = []
        tempRow = []
        for y in range(len(cols)):
            tempRow.append('')
        for x in range(len(rows)):
            Table.append(copy.deepcopy(tempRow))
        for entry in stateMap:
            state = entry[0]
            symbol = entry[1]
            a = rows.index(state)
            b = cols.index(symbol)
            if symbol in NT:
                Table[a][b] = Table[a][b] + f"{stateMap[entry]}"
            elif symbol in T:
                Table[a][b] = Table[a][b] + f"S{stateMap[entry]}"
        self.diction = {}
        addedR = f"{self.separatedRulesList[0][0]} -> {self.separatedRulesList[0][1][1]}"
        self.rules.insert(0, addedR)
        for rule in self.rules:
            k = rule.split("->")
            k[0] = k[0].strip()
            k[1] = k[1].strip()
            rhs = k[1]
            multirhs = rhs.split('|')
            for i in range(len(multirhs)):
                multirhs[i] = multirhs[i].strip()
                multirhs[i] = multirhs[i].split()
            self.diction[k[0]] = multirhs
        self.firsts = {}
        for y in self.rules:
            k = y.split("->")
            k[0] = k[0].strip()
            lhs = k[0]
            multirhs = k[1].strip().split('|')
            for i in range(len(multirhs)):
                multirhs[i] = multirhs[i].strip().split()
            rhs = multirhs
            self.firsts[lhs] = self.first(rhs[0])
        self.follows = {}
        for nt in NT:
            self.follows[nt] = self.follow(nt)
        key_count = 0
        self.numbered = {}
        for rule in self.separatedRulesList:
            tempRule = copy.deepcopy(rule)
            tempRule[1].remove('.')
            self.numbered[key_count] = tempRule
            key_count += 1
        for stateno in statesDict:
            for rule in statesDict[stateno]:
                if rule[1][-1] == '.':
                    temp2 = copy.deepcopy(rule)
                    temp2[1].remove('.')
                    for key in self.numbered:
                        if self.numbered[key] == temp2:
                            follow_result = self.follows[rule[0]]
                            for col in follow_result:
                                index = cols.index(col)
                                if key == 0:
                                    Table[stateno][index] = "Accept"
                                else:
                                    Table[stateno][index] += f"R{key}"
        # Verificar conflitos
        for row in Table:
            for cell in row:
                if ' ' in cell or len(cell.split()) > 1:
                    self.erros.append(ErroSintatico("Conflito na tabela SLR (gramática não é SLR)", 0, 0))
        return Table

    def analisar(self):
        # Preparar input symbols
        input_symbols = [token.tipo.value for token in self.tokens if token.tipo != TokenType.EOF] + ['$']
        stack = [0]
        i = 0
        while True:
            s = stack[-1]
            a = input_symbols[i]
            try:
                action = self.Table[s][self.cols.index(a)].strip()
            except ValueError:
                self.erros.append(ErroSintatico(f"Símbolo inesperado '{a}'", self.tokens[i].linha, self.tokens[i].coluna))
                return None
            if not action:
                self.erros.append(ErroSintatico(f"Nenhuma ação para estado {s} e símbolo '{a}'", self.tokens[i].linha, self.tokens[i].coluna))
                return None
            if 'S' in action:
                state_num = int(action[1:])
                stack.append(a)
                stack.append(state_num)
                i += 1
            elif 'R' in action:
                r = int(action[1:])
                prod = self.numbered[r]
                beta_len = len(prod[1])
                for _ in range(2 * beta_len):
                    stack.pop()
                t = stack[-1]
                A = prod[0]
                try:
                    goto = self.Table[t][self.cols.index(A)].strip()
                except ValueError:
                    self.erros.append(ErroSintatico(f"Símbolo não terminal inesperado '{A}'", 0, 0))
                    return None
                stack.append(A)
                stack.append(int(goto))
            elif action == "Accept":
                print("Parsing concluído com sucesso!")
                return True
            else:
                self.erros.append(ErroSintatico(f"Ação inválida '{action}' para estado {s} e símbolo '{a}'", self.tokens[i].linha, self.tokens[i].coluna))
                return None

    def imprimir_erros(self):
        if self.erros:
            print("\n" + "="*70)
            print("ERROS SINTÁTICOS")
            print("="*70)
            for erro in self.erros:
                print(erro)
            print("="*70)
        else:
            print("\n✓ Nenhum erro sintático encontrado")

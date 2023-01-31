import os, shutil

from characterizer.LibrarySettings import LibrarySettings
from characterizer.LogicCell import LogicCell
from characterizer.char_comb import *
from characterizer.char_seq import *

class Characterizer:
    """Main object of Charlib. Keeps track of settings, cells, and results."""
    
    def __init__(self) -> None:
        self.settings = LibrarySettings()
        self.cells = []

    def target_cell(self) -> LogicCell:
        """Get last cell"""
        return self.cells[len(self.cells) - 1]

    def add_cell(self, name, logic, in_ports, out_ports, function):
        # Create a new logic cell
        self.cells.append(LogicCell(name, logic, in_ports, out_ports, function))

    def initialize_work_dir(self):
        if self.settings.run_sim:
            # Clear out the old work_dir if it exists
            if self.settings.work_dir.exists() and self.settings.work_dir.is_dir():
                shutil.rmtree(self.settings.work_dir)
            self.settings.work_dir.mkdir()
        else:
            print("Save previous working directory and files")

    def characterize(self):
        """Iterate through cells and characterize"""        
        os.chdir(self.settings.work_dir)

        for cell in self.cells:
            # Branch to each logic function
            if(cell.logic == 'INV'):
                print ("INV\n")
                #                   [in0, out0]
                expectationList2 = [['01','10'], ['10','01']]
                return runCombIn1Out1(self.settings, cell, expectationList2,"neg")
            elif(self.target_cell.logic == 'BUF'):
                print ("BUF\n")
                #                   [in0, out0]
                expectationList2 = [['01','01'], ['10','10']]
                return runCombIn1Out1(self.settings, cell, expectationList2,"pos")
            elif(self.target_cell.logic == 'AND2'):
                print ("AND2\n")
                #                   [in0, in1, out0]
                expectationList2 = [['01','1','01'], ['10','1','10'],
                                    ['1','01','01'], ['1','10','10']]
                return runCombIn2Out1(self.settings, cell, expectationList2,"pos")
            elif(cell.logic == 'AND3'):
                print ("AND3\n")
                #                   [in0, in1, in2, out0]
                expectationList2 = [['01','1','1','01'], ['10','1','1','10'],
                                    ['1','01','1','01'], ['1','10','1','10'],
                                    ['1','1','01','01'], ['1','1','10','10']]
                return runCombIn3Out1(self.settings, cell, expectationList2,"pos")
            elif(cell.logic == 'AND4'):
                print ("AND4\n")
                #                   [in0, in1, in2, in3,  out0]
                expectationList2 = [['01','1','1','1','01'], ['10','1','1','1','10'],
                                    ['1','01','1','1','01'], ['1','10','1','1','10'],
                                    ['1','1','01','1','01'], ['1','1','10','1','10'],
                                    ['1','1','1','01','01'], ['1','1','1','10','10']]
                return runCombIn4Out1(self.settings, cell, expectationList2,"pos")
            elif(cell.logic == 'OR2'):
                print ("OR2\n")
                #                   [in0, in1, out0]
                expectationList2 = [['01','0','01'], ['10','0','10'],
                                    ['0','01','01'], ['0','10','10']]
                return runCombIn2Out1(self.settings, cell, expectationList2,"pos")
            elif(cell.logic == 'OR3'):
                print ("OR3\n")
                #                   [in0, in1, in2, out0]
                expectationList2 = [['01','0','0','01'], ['10','0','0','10'],
                                    ['0','01','0','01'], ['0','10','0','10'],
                                    ['0','0','01','01'], ['0','0','10','10']]
                return runCombIn3Out1(self.settings, cell, expectationList2,"pos")
            elif(cell.logic == 'OR4'):
                print ("OR4\n")
                #                   [in0, in1, in2, in3, out0]
                expectationList2 = [['01','0','0','0','01'], ['10','0','0','0','10'],
                                    ['0','01','0','0','01'], ['0','10','0','0','10'],
                                    ['0','0','01','0','01'], ['0','0','10','0','10'],
                                    ['0','0','0','01','01'], ['0','0','0','10','10']]
                return runCombIn4Out1(self.settings, cell, expectationList2,"pos")
            elif(cell.logic == 'NAND2'):
                print ("NAND2\n")
                #                   [in0, in1, out0]
                expectationList2 = [['01','1','10'], ['10','1','01'],
                                    ['1','01','10'], ['1','10','01']]
                return runCombIn2Out1(self.settings, cell, expectationList2,"neg")
            elif(cell.logic == 'NAND3'):
                print ("NAND3\n")
                #                   [in0, in1, in2, out0]
                expectationList2 = [['01','1','1','10'], ['10','1','1','01'],
                                    ['1','01','1','10'], ['1','10','1','01'],
                                    ['1','1','01','10'], ['1','1','10','01']]
                return runCombIn3Out1(self.settings, cell, expectationList2,"neg")
            elif(cell.logic == 'NAND4'):
                print ("NAND4\n")
                #                   [in0, in1, in2, in3, out0]
                expectationList2 = [['01','1','1','1','10'], ['10','1','1','1','01'],
                                    ['1','01','1','1','10'], ['1','10','1','1','01'],
                                    ['1','1','01','1','10'], ['1','1','10','1','01'],
                                    ['1','1','1','01','10'], ['1','1','1','10','01']]
                return runCombIn4Out1(self.settings, cell, expectationList2,"neg")
            elif(cell.logic == 'NOR2'):
                print ("NOR2\n")
                #                   [in0, in1, out0]
                expectationList2 = [['01','0','10'], ['10','0','01'],
                                    ['0','01','10'], ['0','10','01']]
                return runCombIn2Out1(self.settings, cell, expectationList2,"neg")
            elif(cell.logic == 'NOR3'):
                print ("NOR3\n")
                #                   [in0, in1, in2, out0]
                expectationList2 = [['01','0','0','10'], ['10','0','0','01'],
                                    ['0','01','0','10'], ['0','10','0','01'],
                                    ['0','0','01','10'], ['0','0','10','01']]
                return runCombIn3Out1(self.settings, cell, expectationList2,"neg")
            elif(cell.logic == 'NOR4'):
                print ("NOR4\n")
                #                   [in0, in1, in2, in3, out0]
                expectationList2 = [['01','0','0','0','10'], ['10','0','0','0','01'],
                                    ['0','01','0','0','10'], ['0','10','0','0','01'],
                                    ['0','0','01','0','10'], ['0','0','10','0','01'],
                                    ['0','0','0','01','10'], ['0','0','0','10','01']]
                return runCombIn4Out1(self.settings, cell, expectationList2,"neg")
            elif(cell.logic == 'AO21'):
                print ("AO21\n")
                #                   [in0, in1, in2, out0]
                expectationList2 = [['10','1','0','10'], ['01','1','0','01'],
                                    ['1','10','0','10'], ['1','01','0','01'],
                                    ['0','0','10','10'], ['0','0','01','01']]
                return runCombIn3Out1(self.settings, cell, expectationList2,"pos")
            elif(cell.logic == 'AO22'):
                print ("AO22\n")
                #                   [in0, in1, in2, in3, out0]
                expectationList2 = [['10','1','0','0','10'], ['01','1','0','0','01'],
                                    ['1','10','0','0','10'], ['1','01','0','0','01'],
                                    ['0','0','10','1','10'], ['0','0','01','1','01'],
                                    ['0','0','1','10','10'], ['0','0','1','01','01']]
                return runCombIn4Out1(self.settings, cell, expectationList2,"pos")
            elif(cell.logic == 'OA21'):
                print ("OA21\n")
                #                   [in0, in1, in2, out0]
                expectationList2 = [['10','0','1','10'], ['01','0','1','01'],
                                    ['0','10','1','10'], ['0','01','1','01'],
                                    ['0','1','10','10'], ['0','1','01','01']]
                return runCombIn3Out1(self.settings, cell, expectationList2,"pos")
            elif(cell.logic == 'OA22'):
                print ("OA22\n")
                #                   [in0, in1, in2, in3, out0]
                expectationList2 = [['10','1','0','1','10'], ['01','1','0','1','01'],
                                    ['0','10','0','1','10'], ['0','01','0','1','01'],
                                    ['0','1','10','0','10'], ['0','1','01','0','01'],
                                    ['0','1','0','10','10'], ['0','1','0','10','01']]
                return runCombIn4Out1(self.settings, cell, expectationList2,"pos")
            elif(cell.logic == 'AOI21'):
                print ("AOI21\n")
                #                   [in0, in1, in2, out0]
                expectationList2 = [['10','1','0','01'], ['01','1','0','10'],
                                    ['1','10','0','01'], ['1','01','0','10'],
                                    ['0','0','10','01'], ['0','0','01','10']]
                return runCombIn3Out1(self.settings, cell, expectationList2,"neg")
            elif(cell.logic == 'AOI22'):
                print ("AOI22\n")
                #                   [in0, in1, in2, in3, out0]
                expectationList2 = [['10','1','0','0','01'], ['01','1','0','0','10'],
                                    ['1','10','0','0','01'], ['1','01','0','0','10'],
                                    ['0','0','10','1','01'], ['0','0','01','1','10'],
                                    ['0','0','1','10','01'], ['0','0','1','01','10']]
                return runCombIn4Out1(self.settings, cell, expectationList2,"neg")
            elif(cell.logic == 'OAI21'):
                print ("OAI21\n")
                #                   [in0, in1, in2, out0]
                expectationList2 = [['10','0','1','01'], ['01','0','1','10'],
                                    ['0','10','1','01'], ['0','01','1','10'],
                                    ['0','1','10','01'], ['0','1','01','10']]
                return runCombIn3Out1(self.settings, cell, expectationList2,"neg")
            elif(cell.logic == 'OAI22'):
                print ("OAI22\n")
                #                   [in0, in1, in2, in3, out0]
                expectationList2 = [['10','1','0','1','01'], ['01','1','0','1','10'],
                                    ['0','10','0','1','01'], ['0','01','0','1','10'],
                                    ['0','1','10','0','01'], ['0','1','01','0','10'],
                                    ['0','1','0','10','01'], ['0','1','0','10','10']]
                return runCombIn4Out1(self.settings, cell, expectationList2,"neg")

            elif(cell.logic == 'XOR2'):
                print ("XOR2\n")
                #                   [in0, in1, out0]
                expectationList2 = [['01','0','01'], ['10','0','10'],
                                    ['01','1','10'], ['10','1','01'],
                                    ['0','01','01'], ['0','10','10'],
                                    ['1','01','10'], ['1','10','01']]
                return runCombIn2Out1(self.settings, cell, expectationList2,"pos")
            elif(cell.logic == 'XNOR2'):
                print ("XNOR2\n")
                #                   [in0, in1, out0]
                expectationList2 = [['01','0','10'], ['10','0','01'],
                                    ['01','1','01'], ['10','1','10'],
                                    ['0','01','10'], ['0','10','01'],
                                    ['1','01','01'], ['1','10','10']]
                return runCombIn2Out1(self.settings, cell, expectationList2,"pos")
            elif(cell.logic == 'SEL2'):
                print ("SEL2\n")
                #                   [in0, in1, sel, out]
                expectationList2 = [['01','0','0','01'], ['10','0','0','10'],
                                    ['0','01','1','01'], ['0','10','1','10'],
                                    ['1','0','01','10'], ['1','0','10','01'],
                                    ['0','1','01','01'], ['0','1','10','10']]
                return runCombIn3Out1(self.settings, cell, expectationList2,"pos")
            elif(cell.logic == 'HA'):
                print ("HA\n")
                #                   [in0, in1, cout, sum]
                expectationList2 = [['01','0','0','01'],  ['10','0','0','10'],
                                    ['0','01','0','01'],  ['0','10','0','10'],
                                    ['01','1','01','10'], ['10','1','10','10'],
                                    ['1','01','01','10'], ['1','10','10','01']]
                return runCombIn2Out2(self.settings, cell, expectationList2,"pos")
            elif(cell.logic == 'FA'):
                print ("FA\n")
                ##                  [in0, in1, sel, cout, sum]
                expectationList2 = [['01','0','0','0','01'],  ['10','0','0','0','10'],
                                    ['0','01','0','0','01'],  ['0','10','0','0','10'],
                                    ['0','0','01','0','01'],  ['0','0','10','0','10'],
                                    ['01','1','0','01','10'], ['10','1','0','10','01'],
                                    ['01','0','1','01','10'], ['10','0','1','10','01'],
                                    ['1','01','0','01','10'], ['1','10','0','10','01'],
                                    ['0','01','1','01','10'], ['0','10','1','10','01'],
                                    ['1','0','01','01','10'], ['1','0','10','10','01'],
                                    ['0','1','01','01','10'], ['0','1','10','10','01'],
                                    ['01','1','1','1','01'],  ['10','1','1','1','10'],
                                    ['1','01','1','1','01'],  ['1','10','1','1','10'],
                                    ['1','1','01','1','01'],  ['1','1','10','1','10']]
                return runCombIn3Out2(self.settings, cell, expectationList2,"pos")

            ## Branch to sequential logics
            elif(cell.logic == 'DFF_PCPU'):
                print ("DFF, positive clock, positive unate\n")
                ## D1 & C01 -> Q01
                ## D0 & C01 -> Q10
                #                   [D,   C,     Q]
                expectationList2 = [['01','0101','01'],
                                    ['10','0101','10']]
                return runFlop(self.settings, cell, expectationList2)
            elif(cell.logic == 'DFF_PCNU'):
                print ("DFF, positive clock, negative unate\n")
                ## D1 & C01 -> Q01
                ## D0 & C01 -> Q10
                #                   [D,   C,     Q]
                expectationList2 = [['01','0101','10'],
                                    ['10','0101','01']]
                return runFlop(self.settings, cell, expectationList2)
            elif(cell.logic == 'DFF_NCPU'):
                print ("DFF, negative clock, positive unate\n")
                ## D1 & C01 -> Q01
                ## D0 & C01 -> Q10
                #                   [D,   C,     Q]
                expectationList2 = [['01','1010','01'],
                                    ['10','1010','10']]
                return runFlop(self.settings, cell, expectationList2)
            elif(cell.logic == 'DFF_NCNU'):
                print ("DFF, negative clock, negative unate\n")
                ## D1 & C01 -> Q01
                ## D0 & C01 -> Q10
                #                   [D,   C,     Q]
                expectationList2 = [['01','1010','10'],
                                    ['10','1010','01']] 
                return runFlop(self.settings, cell, expectationList2)
            elif(cell.logic == 'DFF_PCPU_NR'):
                print ("DFF, positive clock, positive unate, async neg-reset\n")
                ## D1 & C01 -> Q01
                ## D0 & C01 -> Q10
                ## R01      -> Q10
                #                   [D,   C,    R,    Q]
                expectationList2 = [['01','0101', '1','01'],
                                    ['10','0101', '1','10'],
                                    [ '1','0101','01','10']]
                return runFlop(self.settings, cell, expectationList2)
            elif(cell.logic == 'DFF_PCPU_NRNS'):
                print ("DFF, positive clock, positive unate, async neg-reset, async neg-set\n")
                ## D1 & C01 -> Q01 QN10
                ## D0 & C01 -> Q10 QN01
                ## S01      -> Q01 QN10
                ## R01      -> Q10 QN01
                ##                  [D,   C,  S,   R,    Q]
                expectationList2 = [['01','0101','1', '1', '01'],
                                    ['10','0101','1', '1', '10'],
                                    ['0','0101','01', '1', '01'],
                                    ['1','0101', '1','01', '10']]
                return runFlop(self.settings, cell, expectationList2)
            else:
                print ("Target logic:"+cell.logic+" is not registered for characterization!\n")
                print ("Add characterization function for this program! -> die\n")
                exit()

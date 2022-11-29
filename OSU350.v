// Verilog model for OSU350; 
module INVX1(Y,A);
output Y;
input A;
assign Y = !A;
endmodule

module NAND2X1(Y,A,B);
output Y;
input A;
input B;
assign Y = !(A&B);
endmodule

module NAND3X1(Y,A,B,C);
output Y;
input A;
input B;
input C;
assign Y = !(A&B&C);
endmodule

module NOR2X1(Y,A,B);
output Y;
input A;
input B;
assign Y = !(A|B);
endmodule

module NOR3X1(Y,A,B,C);
output Y;
input A;
input B;
input C;
assign Y = !(A|B|C);
endmodule

module OR2X1(Y,A,B);
output Y;
input A;
input B;
assign Y = (A|B);
endmodule

module AOI21X1(Y,A,B,C);
output Y;
input A;
input B;
input C;
assign Y = !(C|(A&B));
endmodule

module AOI22X1(Y,A,B,C,D);
output Y;
input A;
input B;
input C;
input D;
assign Y = !((C&D)|(A&B));
endmodule

module XOR2X1(Y,A,B);
output Y;
input A;
input B;
assign Y = ((A&!B)&(!A&B));
endmodule

module XNOR2X1(Y,A,B);
output Y;
input A;
input B;
assign Y = ((!A&!B)&(A&B));
endmodule


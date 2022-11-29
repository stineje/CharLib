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


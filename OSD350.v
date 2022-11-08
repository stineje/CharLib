// Verilog model for OSD350; 
module XOR2X1(Y,A,B);
output Y;
input A;
input B;
assign Y = ((A&!B)&(!A&B));
endmodule


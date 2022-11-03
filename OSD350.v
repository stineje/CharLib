// Verilog model for OSD350; 
module AND2X1(Y,A,B);
output Y;
input A;
input B;
assign Y = (A&B);
endmodule


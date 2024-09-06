#include "perimeter.h"
#include <U8x8lib.h>
#include <SoftwareSerial.h>    // need to transfer data to pi

#define pinPerimeterRight A8       // perimeter
#define pinPerimeterLeft A9
#define LEDRight A10
#define LEDLeft A11
#define OLEDSCL A5
#define OLEDSDA A4
#define OLEDRESET A3

String result ="";
unsigned long nextTimePerimeter = 0;
unsigned long nextDisplay = 0;
int perimeterMagRight =0;
int perimeterMagLeft =0;

SoftwareSerial piSerial(0, 1);  // RX,TX 
PerimeterClass perimeter ;

U8X8_SSD1306_128X64_NONAME_SW_I2C u8x8(/* clock=*/ OLEDSCL, /* data=*/ OLEDSDA, /* reset=*/ OLEDRESET);

void setup() {
  
  Serial.begin(9600);
  Serial.println(" ------- Initialize Perimeter Setting ------- ");
  perimeter.begin(pinPerimeterLeft, pinPerimeterRight);
  pinMode(LEDRight,OUTPUT);
  pinMode(LEDLeft,OUTPUT);
  digitalWrite(LEDRight,LOW);
  digitalWrite(LEDLeft,LOW);
  piSerial.begin(115200);
  
  u8x8.begin();
  u8x8.setFont(u8x8_font_chroma48medium8_r);
  u8x8.drawString(0, 0, "Setup finished");
  delay(1000);
  u8x8.drawString(0, 0, "               ");

}

void Display(){
  u8x8.drawString(0, 2, " Left= ");
  u8x8.setCursor(9, 2);
  u8x8.print("        ");
  u8x8.setCursor(8, 2);
  u8x8.print(perimeterMagLeft);
  u8x8.drawString(0, 4, " Right= ");
  u8x8.setCursor(9, 4);
  u8x8.print("        ");
  u8x8.setCursor(8, 4);
  u8x8.print(perimeterMagRight);



}

void loop() {
  
  if  (millis() >= nextTimePerimeter) {
    nextTimePerimeter = millis() +  20;
    //right coil
    perimeterMagRight = perimeter.getMagnitude(1);
    //left coil
    perimeterMagLeft = perimeter.getMagnitude(0);
    result="{'left':"+String(perimeterMagLeft)+",'right':"+String(perimeterMagRight)+"}";
    Serial.println(result);
    piSerial.println(result);     // transfer the data to the pi 
    //Serial.print("Right:");Serial.print(perimeterMagRight);Serial.print(",");Serial.print("Left:");Serial.println(perimeterMagLeft);
    if (perimeterMagRight > 1000){
      digitalWrite(LEDRight,HIGH);
    }else{
      digitalWrite(LEDRight,LOW);
    }
    if (perimeterMagLeft > 1000){
      digitalWrite(LEDLeft,HIGH);
    }else{
      digitalWrite(LEDLeft,LOW);
    }
    
  }
  if (millis() >=nextDisplay){
    nextDisplay=millis()+500;
    Display();
  } 
}

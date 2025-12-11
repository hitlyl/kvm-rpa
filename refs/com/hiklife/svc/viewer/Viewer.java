package com.hiklife.svc.viewer;

import java.awt.Point;
import java.awt.image.BufferedImage;
import javax.swing.JComponent;

import refs.com.hiklife.svc.core.protocol.ProtocolContext;
import refs.com.hiklife.svc.core.protocol.ProtocolHandler;
import refs.com.hiklife.svc.core.protocol.normal.KeyEventPacket;
import refs.com.hiklife.svc.core.protocol.security.SecurityType;
import refs.com.hiklife.svc.viewer.SessionSetting;

public interface Viewer extends SessionSetting {
  void callBackAuthInfo(SecurityType.Type paramType, String paramString1, String paramString2);
  
  void writeKeyEvent(KeyEventPacket[] paramArrayOfKeyEventPacket);
  
  void writeKeyEventByPass(KeyEventPacket[] paramArrayOfKeyEventPacket);
  
  void writeKeyEvent(int paramInt1, int paramInt2);
  
  void writeKeyEvent(KeyEventPacket paramKeyEventPacket);
  
  void writeKeyEventByPass(KeyEventPacket paramKeyEventPacket);
  
  void stopSession();
  
  void writeMouse00();
  
  void writeMouseEvent(Point paramPoint, int paramInt);
  
  void writeMouseEventByPass(Point paramPoint, int paramInt);
  
  void writeKeyStatusRequest();
  
  void writeBroadCastStatusRequest();
  
  void writeBroadCastSetRequest(byte[] paramArrayOfbyte, boolean paramBoolean1, boolean paramBoolean2);
  
  ProtocolHandler getHandler();
  
  ProtocolContext getContext();
  
  JComponent getJComponent();
  
  BufferedImage getCurrentFrame();
  
  void quitSingleMouse();
  
  int getMouseType();
}


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/viewer/Viewer.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */
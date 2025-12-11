package com.hiklife.svc.core.protocol;

import org.apache.mina.core.future.WriteFuture;
import org.apache.mina.core.session.IoSession;

import refs.com.hiklife.svc.core.protocol.InvalidRFBMessageException;
import refs.com.hiklife.svc.core.protocol.ProtocolContext;
import refs.com.hiklife.svc.core.protocol.handler.ProtocolAuthEvent;
import refs.com.hiklife.svc.core.protocol.handler.ProtocolConnectEvent;
import refs.com.hiklife.svc.core.protocol.handler.ProtocolDeviceInfoEvent;
import refs.com.hiklife.svc.core.protocol.handler.ProtocolVMEvent;
import refs.com.hiklife.svc.core.protocol.handler.ProtocolViewerEvent;
import refs.com.hiklife.svc.core.protocol.normal.AudioParamPacket;
import refs.com.hiklife.svc.core.protocol.normal.KeyEventPacket;
import refs.com.hiklife.svc.core.protocol.normal.MouseEventPacket;
import refs.com.hiklife.svc.core.protocol.normal.MouseTypePacket;
import refs.com.hiklife.svc.core.protocol.normal.VideoParamPacket;
import refs.com.hiklife.svc.core.protocol.normal.decoder.FFmpegDecoder;
import refs.com.hiklife.svc.core.protocol.normal.decoder.G726Decoder;
import refs.com.hiklife.svc.core.protocol.security.SecurityType;
import refs.com.hiklife.svc.core.protocol.vm.VMReadPacket;

public interface ProtocolHandler extends FFmpegDecoder.Event, G726Decoder.Event {
  void onConnectSuccess();
  
  void addConnectEvent(ProtocolConnectEvent paramProtocolConnectEvent);
  
  ProtocolConnectEvent getConnectEvent();
  
  void addDeviceInfoEvent(ProtocolDeviceInfoEvent paramProtocolDeviceInfoEvent);
  
  void addViewerEvent(ProtocolViewerEvent paramProtocolViewerEvent);
  
  void addVMEvent(ProtocolVMEvent paramProtocolVMEvent);
  
  ProtocolVMEvent getVMEvent();
  
  void addAuthEvent(ProtocolAuthEvent paramProtocolAuthEvent);
  
  void graceClose();
  
  void handleProtocolMessage(byte[] paramArrayOfbyte) throws InvalidRFBMessageException;
  
  void writeKeepAlive();
  
  void writeProtocolVersion(byte[] paramArrayOfbyte);
  
  void writeSecurityType(byte[] paramArrayOfbyte);
  
  void writeSecurityPath(byte[] paramArrayOfbyte);
  
  void writeUserAccount(byte[] paramArrayOfbyte);
  
  void writeVncAuth(byte[] paramArrayOfbyte);
  
  void writeRsaAuth(byte[] paramArrayOfbyte);
  
  void writeShareMsg();
  
  WriteFuture writeMouseEvent(byte[] paramArrayOfbyte);
  
  WriteFuture writeKeyEvent(byte[] paramArrayOfbyte);
  
  void writeKeyStateParamRequest();
  
  void writeVideoParamRequest();
  
  void writeAudioParamRequest();
  
  void writeCustomVideoParam(VideoParamPacket paramVideoParamPacket);
  
  void writeCustomAudioParam(AudioParamPacket paramAudioParamPacket);
  
  void writeMouseTypeRequest();
  
  WriteFuture writeCustomMouseType(MouseTypePacket paramMouseTypePacket);
  
  void writeKeyEvent(KeyEventPacket[] paramArrayOfKeyEventPacket);
  
  WriteFuture writeKeyEvent(KeyEventPacket paramKeyEventPacket);
  
  void writeMouseEvent(MouseEventPacket[] paramArrayOfMouseEventPacket);
  
  WriteFuture writeMouseEvent(MouseEventPacket paramMouseEventPacket);
  
  void writeBroadCastStatusRequest();
  
  void writeBroadCastSetRequest(byte[] paramArrayOfbyte);
  
  void writeVMCloseRequest();
  
  void writeVMLinkRequest() throws InvalidRFBMessageException;
  
  void writeVMData(VMReadPacket paramVMReadPacket);
  
  IoSession getSession();
  
  void setSession(IoSession paramIoSession);
  
  void destroy();
  
  void callBackAuthInfo(SecurityType.Type paramType, String paramString1, String paramString2);
  
  ProtocolContext getContext();
  
  boolean isBeforeNormal();
  
  boolean isNormalMessage();
  
  boolean isVersionMessage();
  
  boolean isSecurityTypesMessage();
  
  boolean isCentralizeMessage();
}


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/core/protocol/ProtocolHandler.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */
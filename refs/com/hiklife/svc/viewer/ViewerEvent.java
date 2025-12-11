package com.hiklife.svc.viewer;

import java.awt.Point;
import java.awt.image.BufferedImage;

import refs.com.hiklife.svc.core.protocol.normal.AudioParamPacket;
import refs.com.hiklife.svc.core.protocol.normal.BroadcastSetResultPacket;
import refs.com.hiklife.svc.core.protocol.normal.BroadcastStatusPacket;
import refs.com.hiklife.svc.core.protocol.normal.KeyStatusPacket;
import refs.com.hiklife.svc.core.protocol.normal.MouseTypePacket;
import refs.com.hiklife.svc.core.protocol.normal.VideoParamPacket;
import refs.com.hiklife.svc.core.protocol.security.SecurityType;

public interface ViewerEvent {
  default void onConnectFailed(String msg) {}
  
  void onCaughtException(Throwable paramThrowable);
  
  void onAuthSuccess();
  
  void onAuthFailed(String paramString);
  
  void onRequireAuth(SecurityType.Type paramType);
  
  boolean onWriteMouseEvent(Point paramPoint, int paramInt);
  
  boolean onWriteKeyEvent(int paramInt1, int paramInt2);
  
  default void onAfterInitialisation() {}
  
  default void onReadVideoParam(VideoParamPacket videoParamPacket) {}
  
  default void onReadAudioParam(AudioParamPacket audioParamPacket) {}
  
  default void onReadMouseType(MouseTypePacket mouseTypePacket) {}
  
  default void onReadKeyStatus(KeyStatusPacket keyStatusPacket) {}
  
  default void onFocusGained() {}
  
  default void onReadBroadcastStatus(BroadcastStatusPacket broadcastStatusPacket) {}
  
  default void onReadBroadcastSetResult(BroadcastSetResultPacket broadcastSetResultPacket) {}
  
  default void onBeforeDestroy() {}
  
  default void onAfterDestroy() {}
  
  default void onDrawFirstFrame(BufferedImage bufferedImage) {}
  
  default void onSingleMouseAccessDenied() {}
}


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/viewer/ViewerEvent.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */
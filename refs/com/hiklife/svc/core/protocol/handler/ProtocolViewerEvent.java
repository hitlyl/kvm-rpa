package com.hiklife.svc.core.protocol.handler;

import org.bytedeco.ffmpeg.avutil.AVFrame;

import refs.com.hiklife.svc.core.protocol.normal.AudioParamPacket;
import refs.com.hiklife.svc.core.protocol.normal.BroadcastSetResultPacket;
import refs.com.hiklife.svc.core.protocol.normal.BroadcastStatusPacket;
import refs.com.hiklife.svc.core.protocol.normal.KeyStatusPacket;
import refs.com.hiklife.svc.core.protocol.normal.MouseTypePacket;
import refs.com.hiklife.svc.core.protocol.normal.VideoParamPacket;
import refs.com.hiklife.svc.core.protocol.normal.decoder.EncodingType;

public interface ProtocolViewerEvent {
  void onReadImageInfo(int paramInt1, int paramInt2);
  
  void onChangeImageInfo(int paramInt1, int paramInt2);
  
  void onUpdateFrame(AVFrame paramAVFrame);
  
  default void onUpdateVideoRawStream(byte[] bytes, EncodingType type) {}
  
  void onUpdateAudio(byte[] paramArrayOfbyte);
  
  void onVideoParam(VideoParamPacket paramVideoParamPacket);
  
  void onAudioParam(AudioParamPacket paramAudioParamPacket);
  
  void onReadMouseType(MouseTypePacket paramMouseTypePacket);
  
  void onKeyStatus(KeyStatusPacket paramKeyStatusPacket);
  
  void onBroadcastRequest(BroadcastStatusPacket paramBroadcastStatusPacket);
  
  void onBroadcastSet(BroadcastSetResultPacket paramBroadcastSetResultPacket);
  
  void onWriteCustomMouseType(MouseTypePacket paramMouseTypePacket);
}


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/core/protocol/handler/ProtocolViewerEvent.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */
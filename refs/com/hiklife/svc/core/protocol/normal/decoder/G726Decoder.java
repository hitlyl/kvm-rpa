package com.hiklife.svc.core.protocol.normal.decoder;

public abstract class G726Decoder {
  public abstract void decode(byte[] paramArrayOfbyte, Event paramEvent);
  
  public void destroy() {}
  
  public static interface Event {
    void onAudioDecodeFrame(byte[] param1ArrayOfbyte);
  }
}


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/core/protocol/normal/decoder/G726Decoder.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */
import {
  AbsoluteFill,
  Audio,
  Img,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

const palette = {
  ink: '#3c281d',
  line: '#8e614c',
  paper: '#f5eedf',
  rose: '#b97772',
  cream: '#fffaf0',
  softRose: '#f1d5cc',
};

const Star = ({x, y, delay}: {x: number; y: number; delay: number}) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [delay, delay + 10, 232, 250], [0, 0.75, 0.75, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const scale = spring({fps: 30, frame: Math.max(0, frame - delay), config: {damping: 12, stiffness: 180}});
  return (
    <svg viewBox="0 0 36 36" style={{position: 'absolute', left: x, top: y + Math.sin(frame / 18) * 7, width: 32, opacity, transform: `scale(${scale}) rotate(${frame}deg)`}}>
      <path d="M18 0 L21.5 14.5 L36 18 L21.5 21.5 L18 36 L14.5 21.5 L0 18 L14.5 14.5 Z" fill={palette.rose} />
    </svg>
  );
};

export const EnglishListeningRoomOutro = () => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const logoIn = spring({fps, frame, config: {damping: 17, stiffness: 95}});
  const headlineIn = spring({fps, frame: Math.max(0, frame - 18), config: {damping: 17, stiffness: 100}});
  const subscribeIn = spring({fps, frame: Math.max(0, frame - 75), config: {damping: 14, stiffness: 115}});
  const nextIn = spring({fps, frame: Math.max(0, frame - 136), config: {damping: 16, stiffness: 105}});
  const lineProgress = interpolate(frame, [4, 28], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const fadeOut = interpolate(frame, [durationInFrames - 16, durationInFrames], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const logoFloat = Math.sin(frame / 21) * 6;
  const logoScale = interpolate(logoIn, [0, 1], [0.79, 1]);
  const headlineY = interpolate(headlineIn, [0, 1], [36, 0]);
  const subscribeY = interpolate(subscribeIn, [0, 1], [28, 0]);
  const pulse = 1 + Math.max(0, Math.sin((frame - 135) / 8)) * 0.04;

  return (
    <AbsoluteFill
      style={{
        backgroundColor: palette.paper,
        backgroundImage:
          'radial-gradient(circle at 11% 16%, rgba(255,255,255,.95) 0 1px, transparent 1.5px), radial-gradient(circle at 80% 75%, rgba(60,40,29,.04) 0 1px, transparent 1.5px), linear-gradient(130deg, #fbf5e9 0%, #f3ead9 100%)',
        backgroundSize: '13px 13px, 19px 19px, 100% 100%',
        opacity: fadeOut,
        overflow: 'hidden',
      }}
    >
      <Audio src={staticFile('branding/english-listening-room-outro.wav')} />
      <div style={{position: 'absolute', left: -290, top: 200, width: 870, height: 870, border: `2px solid ${palette.line}`, borderRadius: '50%', opacity: 0.16}} />
      <div style={{position: 'absolute', left: -170, top: 315, width: 635, height: 635, border: `1px solid ${palette.line}`, borderRadius: '50%', opacity: 0.2}} />
      <svg viewBox="0 0 1920 1080" style={{position: 'absolute', inset: 0}}>
        <path d="M504 300 C 810 221, 1280 218, 1662 299" fill="none" stroke={palette.line} strokeWidth="3" strokeLinecap="round" style={{strokeDasharray: 1250, strokeDashoffset: 1250 * (1 - lineProgress)}} />
        <path d="M505 858 C 850 936, 1280 922, 1662 848" fill="none" stroke={palette.line} strokeWidth="3" strokeLinecap="round" style={{strokeDasharray: 1250, strokeDashoffset: 1250 * (1 - lineProgress)}} />
      </svg>

      <div style={{position: 'absolute', left: 126, top: 353, width: 328, height: 328, borderRadius: '50%', padding: 12, background: palette.cream, boxShadow: '0 21px 40px rgba(69,43,30,.16)', transform: `translateY(${logoFloat}px) scale(${logoScale})`}}>
        <div style={{position: 'absolute', inset: 4, border: `2px dashed ${palette.rose}`, borderRadius: '50%', transform: `rotate(${frame / 4}deg)`}} />
        <div style={{width: '100%', height: '100%', borderRadius: '50%', overflow: 'hidden', border: `2px solid ${palette.line}`}}>
          <Img src={staticFile('branding/english_listening_room_avatar_v2.png')} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
        </div>
      </div>
      <div style={{position: 'absolute', left: 102, top: 725, width: 380, textAlign: 'center', color: palette.ink, fontFamily: 'Georgia, serif', fontSize: 18, letterSpacing: 2, fontWeight: 700}}>ENGLISH LISTENING ROOM</div>

      <div style={{position: 'absolute', left: 555, top: 366, color: palette.ink, opacity: headlineIn, transform: `translateY(${headlineY}px)`}}>
        <div style={{fontFamily: 'Georgia, serif', fontSize: 27, letterSpacing: 7, fontWeight: 700, color: palette.line, marginBottom: 18}}>KEEP LEARNING WITH US</div>
        <div style={{fontFamily: 'Georgia, serif', fontSize: 62, lineHeight: 1.02, fontWeight: 700, letterSpacing: -1}}>Real English,</div>
        <div style={{fontFamily: 'Georgia, serif', fontSize: 62, lineHeight: 1.02, fontWeight: 700, letterSpacing: -1}}>one conversation at a time.</div>
        <div style={{width: 132, height: 5, borderRadius: 3, backgroundColor: palette.rose, marginTop: 23, transform: `scaleX(${headlineIn})`, transformOrigin: 'left'}} />
      </div>

      <div style={{position: 'absolute', left: 705, top: 608, width: 625, opacity: subscribeIn, transform: `translateY(${subscribeY}px) scale(${pulse})`, transformOrigin: 'center', textAlign: 'center'}}>
        <div style={{fontFamily: 'Georgia, serif', fontSize: 28, fontStyle: 'italic', color: palette.line, marginBottom: 19}}>Learn with us, a little every day.</div>
        <div style={{display: 'inline-flex', alignItems: 'center', gap: 18, padding: '23px 58px 25px', borderRadius: 48, backgroundColor: palette.rose, boxShadow: '0 11px 0 #8f554f, 0 21px 31px rgba(91,52,42,.21)', color: palette.cream, fontFamily: 'Georgia, serif', fontSize: 42, fontWeight: 700, letterSpacing: 3}}><span style={{fontSize: 29}}>✦</span> SUBSCRIBE <span style={{fontSize: 29}}>✦</span></div>
        <div style={{fontFamily: 'Georgia, serif', fontSize: 25, fontStyle: 'italic', color: palette.line, marginTop: 22}}>Join the room</div>
      </div>

      <div style={{position: 'absolute', left: 705, top: 815, width: 625, display: 'flex', justifyContent: 'center', gap: 18, opacity: nextIn}}>
        <div style={{padding: '11px 18px', borderRadius: 22, border: `2px solid ${palette.line}`, background: 'rgba(255,250,240,.65)', color: palette.line, fontFamily: 'Georgia, serif', fontSize: 18, fontWeight: 700, letterSpacing: 2}}>NEXT VIDEO →</div>
        <div style={{padding: '11px 18px', borderRadius: 22, border: `2px solid ${palette.line}`, background: 'rgba(255,250,240,.65)', color: palette.line, fontFamily: 'Georgia, serif', fontSize: 18, fontWeight: 700, letterSpacing: 2}}>MORE TO EXPLORE →</div>
      </div>

      <Star x={474} y={267} delay={31} />
      <Star x={1652} y={290} delay={45} />
      <Star x={1594} y={844} delay={63} />
      <Star x={483} y={834} delay={76} />
    </AbsoluteFill>
  );
};

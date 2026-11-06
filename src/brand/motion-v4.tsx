import {AbsoluteFill, Audio, Easing, Img, interpolate, Sequence, staticFile, useCurrentFrame} from 'remotion';
import {z} from 'zod';
import spec from '../../configs/branding/motion-v4.json';

export const motionBrandSchema = z.object({
  brand: z.object({name: z.string(), logo: z.string(), introAudio: z.string(), welcomeAudio: z.string(), outroAudio: z.string(), outroVoice: z.string(),
    paper: z.string(), ink: z.string(), accent: z.string(), muted: z.string()}),
  showGuides: z.boolean(),
});
type Props = z.infer<typeof motionBrandSchema>;
export const motionBrandDefaults: Props = {brand: spec.brand, showGuides: false};

const ease = Easing.bezier(.22, 1, .36, 1);
const progress = (frame: number, start: number, duration: number) =>
  interpolate(frame, [start, start + duration], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ease});

const Paper = ({brand, children}: Props & {children: React.ReactNode}) => <AbsoluteFill style={{
  background: brand.paper, color: brand.ink, overflow: 'hidden', fontFamily: 'Georgia, serif',
}}>
  <AbsoluteFill style={{background: `radial-gradient(ellipse at 75% 20%, #fffaf1 0%, transparent 55%), linear-gradient(110deg, ${brand.paper}, #e4e8dc)`}} />
  <AbsoluteFill style={{opacity: .16, backgroundImage: `radial-gradient(${brand.muted} 0.6px, transparent 0.6px)`, backgroundSize: '7px 7px'}} />
  <div style={{position: 'absolute', inset: 56, border: `1px solid ${brand.accent}45`}} />
  {children}
</AbsoluteFill>;

const Word = ({text, frame, from, color}: {text: string; frame: number; from: number; color: string}) => {
  const p = progress(frame, from, 13);
  return <span style={{display: 'inline-block', opacity: p, transform: `translateY(${18 * (1 - p)}px)`, color}}>{text}</span>;
};

const SubscribeInvite = ({brand, outro = false}: Pick<Props, 'brand'> & {outro?: boolean}) => {
  const frame = useCurrentFrame();
  const enter = progress(frame, outro ? 45 : spec.ctaEnterFrame, 15);
  const press = interpolate(frame, [spec.ctaPressFrame - 3, spec.ctaPressFrame, spec.ctaPressFrame + 6,
    spec.ctaBurstFrame + 5, spec.ctaBurstFrame + 12], [1, .94, .94, 1.035, 1],
  {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const cursor = progress(frame, 91, 18);
  const cursorFade = progress(frame, 91, 6) * (1 - progress(frame, 125, 10));
  const burst = Math.max(0, frame - spec.ctaBurstFrame);
  const particles = frame >= spec.ctaBurstFrame ? 1 - progress(frame, spec.ctaBurstFrame + 5, 19) : 0;
  return <div style={{position: 'absolute', left: 862, top: 744, width: 830, opacity: enter,
    transform: `translateY(${24 * (1 - enter)}px)`}}>
    <div style={{fontSize: 30, color: brand.ink}}>{outro ? 'Enjoyed this lesson? Join the room.' : spec.ctaText}</div>
    <div style={{position: 'absolute', left: 0, top: 61, width: 320, height: 78,
      borderRadius: 39, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 17,
      background: frame >= spec.ctaPressFrame ? brand.accent : brand.ink, color: '#fffaf1',
      fontFamily: 'Arial, sans-serif', fontWeight: 700, fontSize: 27, letterSpacing: 3,
      transform: `scale(${press})`, boxShadow: `0 ${frame >= spec.ctaPressFrame && frame < spec.ctaBurstFrame ? 2 : 7}px 0 #183f3633, 0 12px 26px #123f3a15`}}>
      <svg viewBox="0 0 24 24" style={{width: 25, height: 25}}><path d="M6 3 L22 12 L6 21 Z" fill="currentColor" /></svg>
      SUBSCRIBE
    </div>
    <svg viewBox="-100 -100 600 300" style={{position: 'absolute', left: -100, top: -100, width: 600, height: 300, overflow: 'visible', pointerEvents: 'none'}}>
      {Array.from({length: 24}, (_, index) => {
        const angle = index * Math.PI * 2 / 24;
        const speed = 5 + index % 4 * 1.3;
        const radius = burst * speed;
        const x = 160 + Math.cos(angle) * radius;
        const y = 100 + Math.sin(angle) * radius * .64 + burst * burst * .035;
        return <g key={index} transform={`translate(${x} ${y}) rotate(${index * 31 + burst * 5})`} opacity={particles}>
          {index % 3 === 0 ? <path d="M0 -7 L2 -2 L7 0 L2 2 L0 7 L-2 2 L-7 0 L-2 -2Z" fill={brand.accent} />
            : <rect x={-3} y={-5} width={6} height={10} rx={2} fill={index % 2 ? brand.ink : brand.accent} />}
        </g>;
      })}
    </svg>
    <Img src={staticFile('branding/icons/mouse-pointer-2.svg')} style={{position: 'absolute', left: 437 - cursor * 200,
      top: 157 - cursor * 53, width: 38, height: 38, opacity: cursorFade,
      transformOrigin: '6.4px 6.4px',
      transform: `scale(${frame >= spec.ctaPressFrame && frame < spec.ctaBurstFrame ? .9 : 1})`, filter: 'drop-shadow(0 2px 2px #123f3a33)'}} />
  </div>;
};

export const EnglishListeningRoomIntroV4 = ({brand, showGuides}: Props) => {
  const frame = useCurrentFrame();
  const hit = spec.impactFrame;
  const reveal = progress(frame, hit - 12, 12);
  const shift = progress(frame, 8, 25);
  const waveFade = 1 - progress(frame, hit, 12);
  const exit = progress(frame, spec.introFrames - 10, 10);
  const orbit = progress(frame, 3, 38);
  const flourish = (1 - progress(frame, 65, 30)) * progress(frame, 4, 14);
  return <Paper brand={brand} showGuides={showGuides}>
    <Audio src={staticFile(brand.introAudio)} volume={.24} />
    <Sequence from={spec.welcomeFrame}>
      <Audio src={staticFile(brand.welcomeAudio)} />
    </Sequence>
    {/* A playful orbit flourish gathers into the existing warm editorial identity. */}
    <svg viewBox="0 0 1920 1080" style={{position: 'absolute', inset: 0, opacity: flourish}}>
      {[0, 1, 2].map((index) => <ellipse key={index} cx={520} cy={520}
        rx={285 + index * 19} ry={272 + index * 15} fill="none"
        stroke={index === 1 ? brand.ink : brand.accent} strokeWidth={index === 1 ? 2 : 4}
        strokeDasharray={`${(150 + index * 60) * orbit} 2000`}
        transform={`rotate(${frame * (index % 2 ? -3.4 : 2.8) + index * 115} 520 520)`} />)}
      {Array.from({length: 18}, (_, index) => {
        const angle = (index * 137.5 + frame * .6) * Math.PI / 180;
        const radius = 320 + index % 4 * 25;
        const appear = progress(frame, 5 + index % 6 * 2, 14);
        const x = 520 + Math.cos(angle) * radius * (.65 + .35 * orbit);
        const y = 520 + Math.sin(angle) * radius * (.65 + .35 * orbit);
        return <g key={index} transform={`translate(${x} ${y}) rotate(${index * 23 + frame})`} opacity={appear * .7}>
          {index % 3 === 0 ? <path d="M0 -9 L2 -2 L9 0 L2 2 L0 9 L-2 2 L-9 0 L-2 -2Z" fill={brand.accent} />
            : <circle r={index % 2 ? 3 : 5} fill={index % 2 ? brand.ink : brand.accent} />}
        </g>;
      })}
    </svg>
    <div style={{position: 'absolute', left: 960 - shift * 440, top: 494,
      display: 'flex', gap: 13, alignItems: 'center', height: 100, transform: 'translateX(-50%)', opacity: waveFade}}>
      {Array.from({length: 21}, (_, index) => {
        const height = 14 + Math.sin(index * .81 + frame * .18) ** 2 * (96 - Math.abs(index - 10) * 6);
        return <div key={index} style={{width: 5, height, borderRadius: 5, background: index === 10 ? brand.accent : brand.ink}} />;
      })}
    </div>
    <div style={{position: 'absolute', left: 283, top: 237, width: 470, height: 580,
      borderRadius: '245px 245px 22px 22px', border: `1px solid ${brand.accent}`,
      opacity: reveal, transform: `scale(${.84 + .16 * reveal}) rotate(${-5 * (1 - reveal)}deg)`,
      background: `linear-gradient(155deg, #fffaf1, ${brand.paper})`, boxShadow: '0 26px 65px #123f3a12'}}>
      <div style={{position: 'absolute', inset: 18, border: `1px solid ${brand.accent}55`, borderRadius: '230px 230px 10px 10px'}} />
      <div style={{position: 'absolute', left: 57, top: 91, width: 354, height: 354, borderRadius: '50%', overflow: 'hidden', boxShadow: '0 10px 26px #493b2522'}}>
        <Img src={staticFile(brand.logo)} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
      </div>
      <div style={{position: 'absolute', left: 57, width: 354, bottom: 54, display: 'flex', justifyContent: 'center', color: brand.accent,
        fontFamily: 'Arial, sans-serif', fontSize: 17}}>
        <span style={{letterSpacing: 6, paddingLeft: 6, whiteSpace: 'nowrap'}}>A LITTLE EVERY DAY</span>
      </div>
    </div>
    <div style={{position: 'absolute', left: 862, top: 305, width: 870}}>
      <div style={{fontFamily: 'Arial, sans-serif', fontSize: 20, letterSpacing: 7, color: brand.accent,
        opacity: progress(frame, 7, 14), transform: `translateX(${70 * (1 - progress(frame, 7, 22))}px)`}}>HI, WELCOME TO</div>
      <div aria-label={brand.name} style={{marginTop: 27, fontSize: 108, lineHeight: 1.02, letterSpacing: -4,
        opacity: reveal, transform: `translateY(${45 * (1 - reveal)}px)`}}>
        <span style={{display: 'inline-block', transform: `translateX(${90 * (1 - progress(frame, 12, 15))}px)`}}>English</span><br />
        <span style={{display: 'inline-block', transform: `translateX(${130 * (1 - progress(frame, 18, 18))}px)`}}>Listening Room<span style={{color: brand.accent}}>.</span></span>
      </div>
      <div style={{width: 640 * progress(frame, 30, 20), height: 2, background: brand.accent, marginTop: 40}} />
      <div style={{display: 'flex', gap: 28, marginTop: 29, fontFamily: 'Arial, sans-serif', fontSize: 23, letterSpacing: 5}}>
        {['LISTEN', 'NOTICE', 'SPEAK'].map((word, index) => <Word key={word} text={word} frame={frame}
          from={spec.noteFrames[index]} color={index === 1 ? brand.accent : brand.ink} />)}
      </div>
    </div>
    {/* Small light lift at the sound impact; no full-frame strobe. */}
    <AbsoluteFill style={{background: '#fffaf1', opacity: frame >= hit ? .14 * (1 - progress(frame, hit, 6)) : 0}} />
    <div style={{position: 'absolute', left: 283, width: 470, bottom: 108, display: 'flex', justifyContent: 'center',
      fontFamily: 'Arial, sans-serif', fontSize: 14, color: brand.muted, opacity: progress(frame, 42, 15)}}>
      <span style={{letterSpacing: 2.6, paddingLeft: 2.6, whiteSpace: 'nowrap'}}>YOUR NEXT CONVERSATION STARTS HERE</span>
    </div>
    <SubscribeInvite brand={brand} />
    <AbsoluteFill style={{background: brand.paper, opacity: exit}} />
  </Paper>;
};

export const EnglishListeningRoomOutroV4 = ({brand, showGuides}: Props) => {
  const frame = useCurrentFrame();
  const settle = progress(frame, 6, 24);
  return <Paper brand={brand} showGuides={showGuides}>
    <Audio src={staticFile(brand.outroAudio)} volume={.20} />
    <Sequence from={spec.outroVoiceFrame}>
      <Audio src={staticFile(brand.outroVoice)} />
    </Sequence>
    <svg viewBox="0 0 1920 1080" style={{position: 'absolute', inset: 0, opacity: (1 - progress(frame, 70, 25)) * settle}}>
      {[0, 1].map(index => <ellipse key={index} cx={518} cy={522} rx={276 + index * 20} ry={275 + index * 20}
        fill="none" stroke={brand.accent} strokeWidth={2} strokeDasharray="190 1900"
        transform={`rotate(${frame * (index ? -1.6 : 1.9) + index * 180} 518 522)`} />)}
    </svg>
    <div style={{position: 'absolute', left: 283, top: 237, width: 470, height: 580, opacity: settle,
      borderRadius: '245px 245px 22px 22px', border: `1px solid ${brand.accent}`,
      background: `linear-gradient(155deg, #fffaf1, ${brand.paper})`, boxShadow: '0 26px 65px #123f3a12',
      transform: `translateY(${20 * (1 - settle)}px)`}}>
      <div style={{position: 'absolute', inset: 18, borderRadius: '230px 230px 10px 10px', border: `1px solid ${brand.accent}55`}} />
      <Img src={staticFile(brand.logo)} style={{position: 'absolute', left: 57, top: 91, width: 354, height: 354,
        borderRadius: '50%', boxShadow: '0 10px 26px #493b2522'}} />
      <div style={{position: 'absolute', left: 57, width: 354, bottom: 54, display: 'flex', justifyContent: 'center',
        fontFamily: 'Arial, sans-serif', fontSize: 17, color: brand.accent}}>
        <span style={{letterSpacing: 6, paddingLeft: 6, whiteSpace: 'nowrap'}}>A LITTLE EVERY DAY</span>
      </div>
    </div>
    <div style={{position: 'absolute', left: 862, top: 288, width: 900, opacity: settle,
      transform: `translateY(${25 * (1 - settle)}px)`}}>
      <div style={{fontFamily: 'Arial, sans-serif', fontSize: 20, letterSpacing: 6, color: brand.accent}}>SEE YOU NEXT TIME</div>
      <div style={{fontSize: 92, lineHeight: 1.08, letterSpacing: -3, marginTop: 30}}>Thanks for<br />learning with us<span style={{color: brand.accent}}>.</span></div>
      <div style={{height: 2, width: 640 * progress(frame, 20, 25), background: brand.accent, marginTop: 35}} />
      <div style={{fontSize: 35, color: brand.muted, marginTop: 29}}>A little English. Every day.</div>
    </div>
    <div style={{position: 'absolute', left: 283, width: 470, bottom: 108, textAlign: 'center',
      fontFamily: 'Arial, sans-serif', fontSize: 16, letterSpacing: 3, color: brand.muted, opacity: settle}}>{brand.name.toUpperCase()}</div>
    <SubscribeInvite brand={brand} outro />
    <AbsoluteFill style={{background: brand.paper, opacity: progress(frame, spec.outroFrames - 12, 12)}} />
  </Paper>;
};

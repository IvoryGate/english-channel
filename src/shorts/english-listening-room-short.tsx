import React from 'react';
import type {Caption} from '@remotion/captions';
import {AbsoluteFill, Easing, Img, interpolate, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {HorizontalSpectrum, SpectrumData} from './horizontal-spectrum';

export type ShortScene = {
  speaker: string; text: string; startSec: number; endSec: number; caption?: Caption;
};
export type EnglishListeningRoomShortProps = {
  format: 'micro_story' | 'listen_choose' | 'dialogue' | 'classic_cliffhanger';
  cefr: 'A2' | 'B1'; durationSec: number; hook: string; hookEndSec: number;
  scenes: ShortScene[]; prompt: string; answer: string;
  promptStartSec: number; answerStartSec: number;
  backgroundImage: string; brandLogo: string; cta: string; spectrum?: SpectrumData;
};
const labels = {
  micro_story: 'A TINY STORY', listen_choose: 'LISTEN & CHOOSE',
  dialogue: 'REAL-LIFE ENGLISH', classic_cliffhanger: 'STORY TIME',
} as const;
const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

export const EnglishListeningRoomShort: React.FC<EnglishListeningRoomShortProps> = (props) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const second = frame/fps;
  const scene = props.scenes.find(s => second >= s.startSec && second < s.endSec);
  const hook = second < props.hookEndSec;
  const question = !hook && second >= props.promptStartSec && second < props.answerStartSec;
  const answer = !hook && second >= props.answerStartSec;
  const text = hook ? props.hook : answer ? props.answer : question ? props.prompt : scene?.caption?.text ?? scene?.text ?? '';
  const start = hook ? 0 : answer ? props.answerStartSec : question ? props.promptStartSec : scene?.startSec ?? second;
  const entrance = interpolate(second-start, [0, .35], [0, 1], {...clamp, easing: Easing.bezier(.22, 1, .36, 1)});
  const cta = interpolate(second, [props.durationSec-3.2, props.durationSec-2.85], [0, 1], clamp);
  const press = interpolate(second, [props.durationSec-1.6, props.durationSec-1.48, props.durationSec-1.3], [1, .96, 1], clamp);
  const burst = interpolate(second, [props.durationSec-1.48, props.durationSec-.8], [0, 1], clamp);
  const eyebrow = hook ? 'LISTEN CLOSELY' : answer ? 'THE ANSWER' : question ? 'YOUR TURN' :
    scene?.speaker && scene.speaker !== 'narrator' ? scene.speaker.replace(/_/g, ' ').toUpperCase() : 'KEEP LISTENING';
  return <AbsoluteFill style={{backgroundColor: '#FFF9EC', fontFamily: 'Inter, Arial, sans-serif', overflow: 'hidden'}}>
    <Img src={staticFile(props.backgroundImage)} style={{width: '100%', height: '100%', objectFit: 'cover',
      scale: interpolate(frame, [0, durationInFrames], [1.025, 1.065], clamp)}}/>
    <AbsoluteFill style={{background: 'linear-gradient(180deg,rgba(255,250,239,.78) 0%,rgba(255,250,239,.55) 18%,rgba(255,250,239,.24) 32%,transparent 44%,rgba(17,43,37,.18) 70%,rgba(17,43,37,.30) 100%)'}}/>

    <div style={{position: 'absolute', top: 100, left: 100, right: 100, textAlign: 'center', color: '#133F39'}}>
      <Img src={staticFile(props.brandLogo)} style={{width: 208, height: 208, borderRadius: '50%',
        boxShadow: '0 8px 24px rgba(82,54,33,.20)'}}/>
      <div style={{fontFamily: 'Georgia, Times New Roman, serif', fontSize: 57, fontWeight: 700,
        lineHeight: 1.12, letterSpacing: -1.3, marginTop: 18}}>English Listening Room</div>
      <div style={{fontSize: 27, letterSpacing: 4.8, color: '#9F693D', marginTop: 17}}>A LITTLE EVERY DAY</div>
      <div style={{fontSize: 27, fontWeight: 700, letterSpacing: 2.5, marginTop: 24, opacity: 1-cta}}>
        {labels[props.format]} <span style={{color: '#9F693D'}}> / {props.cefr}</span>
      </div>
    </div>

    {text ? <div aria-label={text} style={{position: 'absolute', left: 100, right: 100,
      top: interpolate(cta, [0, 1], [1010, 710]), translate: '0 -50%', textAlign: 'center',
      opacity: hook ? 1 : entrance}}>
      <div style={{color: '#FFF4CD', fontSize: 31, fontWeight: 700, letterSpacing: 3,
        marginBottom: 20, textShadow: '0 2px 5px #173A30,0 3px 14px #173A3099'}}>{eyebrow}</div>
      <div style={{color: '#FFFFFF', fontFamily: 'Georgia, Times New Roman, serif',
        fontSize: hook ? 86 : interpolate(cta, [0, 1], [82, 62]), fontWeight: 700, lineHeight: 1.17, letterSpacing: -.6,
        WebkitTextStroke: '1.2px rgba(15,38,34,.68)', paintOrder: 'stroke fill',
        textShadow: '0 3px 4px rgba(15,38,34,.8),0 5px 20px rgba(15,38,34,.6)',
        translate: `0 ${hook ? 0 : 12*(1-entrance)}px`}}>{text}</div>
      {question ? <div style={{color: '#FFF4CD', fontSize: 35, marginTop: 22,
        textShadow: '0 2px 6px #173A30'}}>Your answer in {Math.max(0, Math.ceil(props.answerStartSec-second))}s</div> : null}
    </div> : null}

    <div style={{position: 'absolute', left: 100, right: 100, top: '53%', translate: '0 -50%',
      opacity: cta, textAlign: 'center', color: '#fff'}}>
      <div style={{fontFamily: 'Georgia, serif', fontSize: 62, fontWeight: 700, lineHeight: 1.1,
        textShadow: '0 3px 4px #173A30,0 5px 20px #173A3099'}}>Thanks for listening.</div>
      <div style={{fontSize: 37, lineHeight: 1.2, marginTop: 20, marginBottom: 30,
        textShadow: '0 2px 6px #173A30'}}>{props.cta}</div>
      <div style={{display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
        position: 'relative', width: 560, height: 132, borderRadius: 999, background: '#E85B4D',
        boxShadow: '0 12px 32px rgba(123,40,28,.28)', fontSize: 58, fontWeight: 800, letterSpacing: 2,
        scale: press}}>SUBSCRIBE
        {Array.from({length: 14}, (_, i) => {
          const angle = i*Math.PI/7;
          return <span key={i} style={{position: 'absolute', left: '50%', top: '50%', width: 9, height: 9,
            borderRadius: '50%', background: i%2 ? '#FFF2C7' : '#A1F2DE', opacity: burst > 0 && burst < 1 ? 1-burst : 0,
            translate: `${Math.cos(angle)*(260+80*burst)}px ${Math.sin(angle)*(65+100*burst)}px`}}/>;
        })}
      </div>
    </div>

    <div style={{position: 'absolute', left: 100, right: 100, bottom: 265, height: 230}}>
      <HorizontalSpectrum data={props.spectrum} second={second}/>
    </div>
  </AbsoluteFill>;
};

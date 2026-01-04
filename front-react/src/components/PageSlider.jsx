import { useState } from 'react';
import { CSSTransition, SwitchTransition } from 'react-transition-group';
import GameStart from './GameStart';
import InGame from './InGame';
import '../styles/PageSlider.css';

export default function PageSlider() {
  const [index, setIndex] = useState(0);

  // 페이지 개수는 고정 (GameStart, InGame)
  const PAGE_COUNT = 2;

  const nextPage = () => {
    setIndex((prev) => (prev + 1) % PAGE_COUNT);
  };

  const pages = [<GameStart onGameStart={nextPage} />, <InGame />];

  return (
    <div className="page-slider-container">
      <div className="page-container">
        <SwitchTransition>
          <CSSTransition key={index} timeout={500} classNames="fade">
            <div className="page-wrapper">{pages[index]}</div>
          </CSSTransition>
        </SwitchTransition>
      </div>
    </div>
  );
}

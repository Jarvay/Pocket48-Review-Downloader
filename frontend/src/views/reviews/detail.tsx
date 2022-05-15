import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { ApiInstance } from '../../services/api';
import { Card, Layout } from 'antd';
import { LiveType } from '../../services/enums';
import VideoJs from 'video.js';

const ReviewDetail: React.FC = (props) => {
  const [review, setReview] = useState<any>();

  const routeParams = useParams<{ id: string }>();

  const renderRadio = () => {
    return null;
  };

  const renderLive = () => {
    return (
      <video
        id={`video-js-${review?.liveId}`}
        className="video video-js"
        preload="auto"
      >
        <source src={review?.playStreamPath} />
      </video>
    );
  };

  useEffect(() => {
    ApiInstance.getOne({ liveId: routeParams.id }).then((result) => {
      setReview(result.content);
    });

    const videoJsPlayer = VideoJs('video-js-' + review?.liveId, {
      autoplay: false, // 自动播放
      controls: true, // 是否显示控制栏
      techOrder: ['html5'], // 兼容顺序
      sourceOrder: true, //
      sources: [
        {
          src: review?.playStreamPath,
        },
      ],
      playbackRates: [
        0.5, 0.75, 1, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0, 3.5, 4, 4.5, 5,
      ],
    });
  }, [routeParams.id, review]);

  return (
    <Layout>
      <Card>
        <Card>
          {review?.liveType === LiveType.Radio ? renderRadio() : renderLive()}
        </Card>

        <Card></Card>
      </Card>
    </Layout>
  );
};

export default ReviewDetail;

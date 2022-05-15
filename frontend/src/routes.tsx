import { PathRouteProps } from 'react-router/lib/components';
import { ItemType } from 'antd/es/menu/hooks/useItems';
import Lives from './views/lives';
import Reviews from './views/reviews';
import ReviewDetail from './views/reviews/detail';

export const routes: (PathRouteProps & ItemType & { hide?: boolean })[] = [
  {
    key: 'lives',
    path: '/lives',
    element: <Lives />,
    label: '直播',
  },
  {
    key: 'reviews',
    path: '/reviews',
    element: <Reviews />,
    label: '回放',
  },
  {
    key: 'review',
    path: '/reviews/:id',
    element: <ReviewDetail />,
    label: '回放',
    hide: true,
  },
];

import React, { useEffect, useState } from 'react';
import {
  Avatar,
  Button,
  Card,
  Layout,
  List,
  Select,
  Skeleton,
  Space,
  Tag,
} from 'antd';
import { ApiInstance } from '../../services/api';
import Utils from '../../services/utils';
import { PlaySquareOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';

const { Meta } = Card;
const { Header, Content } = Layout;

const Reviews: React.FC = () => {
  const [initLoading, setInitLoading] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);
  const [dataSource, setDataSource] = useState<any[]>([]);
  const [next, setNext] = useState<string>('0');

  const navigate = useNavigate();

  const onLoadMore = async () => {
    setLoading(true);
    try {
      const { content } = await ApiInstance.reviewsPage({
        next,
      });
      const liveList = content.liveList.map((item: any) => {
        item.team = Utils.team(item.userInfo?.userId);
        return item;
      });
      console.log('liveList', liveList);
      setDataSource(dataSource.concat(liveList));
      setNext(content.next);
      setLoading(false);
    } catch (e) {
      console.error(e);
      setLoading(false);
    }
  };

  const loadMore =
    !initLoading && !loading ? (
      <div
        style={{
          textAlign: 'center',
          marginTop: 12,
          height: 32,
          lineHeight: '32px',
        }}
      >
        <Button onClick={onLoadMore}>loading more</Button>
      </div>
    ) : null;

  useEffect(() => {
    onLoadMore().then();
  }, []);

  return (
    <Layout>
      <Content>
        <List
          grid={{
            gutter: 16,
            xs: 1,
            sm: 2,
            md: 4,
            lg: 4,
            xl: 6,
            xxl: 8,
          }}
          loading={loading}
          dataSource={dataSource}
          loadMore={loadMore}
          renderItem={(item) => (
            <List.Item>
              <Card
                bordered
                cover={
                  <div
                    style={{
                      width: '100%',
                      height: 0,
                      paddingTop: '100%',
                      position: 'relative',
                    }}
                  >
                    <img
                      style={{
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        width: '100%',
                        height: '100%',
                      }}
                      src={Utils.sourceUrl(item.coverPath)}
                    />
                  </div>
                }
                actions={[
                  <PlaySquareOutlined
                    key="play"
                    onClick={() => {
                      navigate('/reviews/' + item.liveId);
                    }}
                  />,
                ]}
              >
                <Meta
                  avatar={
                    <Avatar src={Utils.sourceUrl(item.userInfo?.avatar)} />
                  }
                  title={item.title}
                  description={
                    <>
                      <Space direction="vertical">
                        <Tag color={`#${item.team.teamColor}`}>
                          {item.team.teamName}
                        </Tag>
                        <span>{item?.userInfo.nickname}</span>
                      </Space>
                    </>
                  }
                />
              </Card>
            </List.Item>
          )}
        />
      </Content>
    </Layout>
  );
};

export default Reviews;

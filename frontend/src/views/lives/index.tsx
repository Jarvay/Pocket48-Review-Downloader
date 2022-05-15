import React, { useState } from 'react';
import { Avatar, Button, Card, Layout, List, Skeleton } from 'antd';
import { ApiInstance } from '../../services/api';
import Utils from '../../services/utils';

const { Meta } = Card;

const Lives: React.FC = () => {
  const [initLoading, setInitLoading] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);
  const [dataSource, setDataSource] = useState<any[]>([]);

  const onLoadMore = async () => {
    const { content } = await ApiInstance.lives();
    setDataSource(content.liveList);
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

  return (
    <Layout>
      <List
        grid={{
          gutter: 16,
          column: 8,
        }}
        dataSource={dataSource}
        loadMore={loadMore}
        renderItem={(item) => (
          <Card
            bordered
            cover={
              <div
                style={{
                  width: 256,
                  height: 0,
                  paddingBottom: '60%',
                  position: 'relative',
                }}
              >
                <img
                  style={{
                    width: '100%',
                    height: '100%',
                    position: 'absolute',
                  }}
                  src={Utils.sourceUrl(item.coverPath)}
                />
              </div>
            }
            // actions={[
            //   <SettingOutlined key="setting" />,
            //   <EditOutlined key="edit" />,
            //   <EllipsisOutlined key="ellipsis" />,
            // ]}
          >
            <Meta
              avatar={<Avatar src={Utils.sourceUrl(item.userInfo?.avatar)} />}
              title={item.title}
            />
          </Card>
        )}
      />
    </Layout>
  );
};

export default Lives;

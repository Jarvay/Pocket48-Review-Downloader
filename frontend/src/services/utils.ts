export default class Utils {
  public static sourceUrl(sourcePath: string) {
    if (sourcePath.includes('http')) {
      return sourcePath;
    } else {
      return 'https://source.48.cn' + sourcePath;
    }
  }

  public static sourceUrls(sourcePaths: string[]) {
    return sourcePaths.map((picture) => Utils.sourceUrl(picture));
  }

  public static setInformation(information: any) {
    localStorage.setItem('information', JSON.stringify(information));
  }

  public static getInformation() {
    try {
      return JSON.parse(localStorage.getItem('information') || '');
    } catch (e) {
      console.error(e);
      return null;
    }
  }

  public static user(userId: string) {
    const information = Utils.getInformation();
    if (!information) return null;
    return information.starInfo.find(
      (item: any) => String(item.userId) === String(userId)
    );
  }

  public static team(userId: string) {
    const information = Utils.getInformation();
    if (!information) return null;
    const user = Utils.user(userId);
    console.log('user', user);
    return information.teamInfo.find(
      (item: any) => String(item.teamId) === String(user?.teamId)
    );
  }
}

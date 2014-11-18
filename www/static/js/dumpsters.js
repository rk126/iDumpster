/**
 * @jsx React.DOM
 */
var Dumpster = React.createClass({
  render: function() {
    return (
      <tr>
        <td>{this.props.name}</td>
        <td>{this.props.location}</td>
        <td>{this.props.value}</td>
      </tr>
    );
  }
});

var DumpsterTable = React.createClass({
  loadStatusFromServer: function() {
    $.ajax({
      url: this.props.url,
      dataType: 'json',
      success: function(data) {
        this.setState({data: data});
      }.bind(this),
      error: function(xhr, status, err) {
        console.error(this.props.url, status, err.toString());
      }.bind(this)
    });
  },
  getInitialState: function() {
    return {data: []};
  },
  componentDidMount: function() {
    this.loadStatusFromServer();
    setInterval(this.loadStatusFromServer, this.props.pollInterval);
  },
  render: function() {
    return (
      <div className="table-responsive">
        <table className="table table-striped">
          <thead>
            <tr>
              <th>Name</th>
              <th>Location</th>
              <th>Value</th>
            </tr>
          </thead>
          <tbody>
            <DumpsterList data={this.state.data} />
          </tbody>
        </table>
      </div>
    );
  }
});

var DumpsterList = React.createClass({
  render: function() {
    var dumpsterNodes = this.props.data.map(function(dumpster, index) {
      return (
        // `key` is a React-specific concept and is not mandatory for the
        // purpose of this tutorial. if you're curious, see more here:
        // http://facebook.github.io/react/docs/multiple-components.html#dynamic-children
        <Dumpster name={dumpster.name} location={dumpster.location} value={dumpster.value} key={index} />
      );
    });
    return (
      <div className="dumpsterList">
        {dumpsterNodes}
      </div>
    );
  }
});

React.renderComponent(
  <DumpsterTable url="dumpsters.json" pollInterval={2000} />,
  document.getElementById('dumpsters')
);
